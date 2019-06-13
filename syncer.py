#!/usr/bin/python

import argparse
import fcntl
import os
import select
import subprocess

# Directory at this host where to watch file changes.
source_dir = '/home/username/projects/my-project/'

# Directory at the target host where to upload files.
target_dir = '/usr/local/lib/my-project/'

# Target host where to upload files via rsync.
# Set up credentials in your .ssh/config file.
target_host = 'my.domain.com'

# FSWatch arguments.
fswatch_exclude = ['jb_tmp', 'jb_old', r'\.idea', r'\.git', r'\.pyc$']
fswatch_args = ['fswatch', '--print0', '--latency=1'] + ['--exclude=%s' % x for x in fswatch_exclude]

# Rsync arguments.
rsync_exclude = ['jb_tmp', 'jb_old', r'.idea', r'.git', r'*.pyc']
rsync_args = ['rsync', '-avz'] + ['--exclude=%s' % x for x in rsync_exclude]


def rsync_upload(verbose=False):
    # Upload directory via rsync.
    print('Uploading directory %s' % source_dir)
    rsync_stdout = None if verbose else subprocess.PIPE
    rsync_cmd = rsync_args + [source_dir, '%s:%s' % (target_host, target_dir)]
    status = subprocess.call(rsync_cmd, stdin=subprocess.PIPE, stdout=rsync_stdout)

    if status == 0:
        print('Uploading completed')
    else:
        print('Error syncing file(s)')


def rsync_download(verbose=False):
    # Download directory via rsync.
    print('Downloading directory %s' % source_dir)
    rsync_stdout = None if verbose else subprocess.PIPE
    rsync_cmd = rsync_args + ['%s:%s' % (target_host, target_dir), source_dir]
    status = subprocess.call(rsync_cmd, stdin=subprocess.PIPE, stdout=rsync_stdout)

    if status == 0:
        print('Downloading completed')
    else:
        print('Error syncing file(s)')


def watch_and_upload(verbose=False):
    # Start watching FS events.
    print('Watching directory %s' % source_dir)
    fswatch = subprocess.Popen(fswatch_args + [source_dir], stdout=subprocess.PIPE)
    fcntl.fcntl(fswatch.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

    # This is endless script.
    while True:
        # Wait the next chunk in fswatch stdout.
        select.select([fswatch.stdout.fileno()], [], [])

        # Next chunk ready to read.
        data = fswatch.stdout.read()
        files = []

        # Fswatch responsed something. Read and check it.
        for file_name in data.split('\x00'):
            # Rsync could not sync file with "\n" in name.
            if '\n' in file_name:
                continue

            # Check that file with this name exists.
            if not os.path.isfile(file_name):
                continue

            # Make relative path from absolute
            file_name = file_name.replace(source_dir, '')

            # Ok. Next we sync the file.
            print('Adding file %s' % file_name)
            files.append(file_name)

        # Files ready to rsync. Call rsync and wait the result.
        if files:
            rsync_stdout = None if verbose else subprocess.PIPE
            rsync_cmd = rsync_args + ['--files-from=/dev/stdin', source_dir, '%s:%s' % (target_host, target_dir)]
            rsync = subprocess.Popen(rsync_cmd, stdin=subprocess.PIPE, stdout=rsync_stdout)
            rsync.stdin.write('\n'.join(files))
            rsync.stdin.close()
            status = rsync.wait()

            if status == 0:
                print('Synced %d file(s)' % len(files))
            else:
                print('Error syncing file(s)')

            files[:] = []


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--upload',  action='store_true')
    parser.add_argument('--download',  action='store_true')
    parser.add_argument('--watch',  action='store_true')
    parser.add_argument('--verbose',  action='store_true')
    args = parser.parse_args()

    if args.upload:
        rsync_upload(args.verbose)
    elif args.download:
        rsync_download(args.verbose)
    elif args.watch:
        watch_and_upload(args.verbose)
    else:
        parser.print_help()
