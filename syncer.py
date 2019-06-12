#!/usr/bin/python

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

fswatch_exclude = ['jb_tmp', 'jb_old', r'\.idea', r'\.git', r'\.pyc$']
fswatch_args = ['fswatch', '--print0', '--latency=1'] + ['--exclude=%s' % x for x in fswatch_exclude]
rsync_args = ['rsync', '-avz', '--files-from=/dev/stdin']

# Start watching FS events.
fswatch = subprocess.Popen(fswatch_args + [source_dir], stdout=subprocess.PIPE)
fcntl.fcntl(fswatch.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
print('Watching directory %s' % source_dir)

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
        rsync_cmd = rsync_args + [source_dir, '%s:%s' % (target_host, target_dir)]
        rsync = subprocess.Popen(rsync_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        rsync.stdin.write('\n'.join(files))
        rsync.stdin.close()
        print('Synced %d file(s)!' % len(files))
        files[:] = []
