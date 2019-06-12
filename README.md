# Python utility to bind the FSWatch and Rsync

h1. The use case

1. You develop the project at your Mac but run it in cloud.
2. After any local change you rsync project files to cloud with hands.

h1. How this tool works

1. It listens FS events (via fswatch).
2. Next it reads the changes chunk (buffered for 1 second).
3. Finally it uploads this files via rsync.

h1. Example

```bash
my-project $ python2.7 syncer

Watching directory /Users/p.patrin/Projects/my-project/
Adding file web/data/models.py
Adding file web/data/services.py
Adding file web/data/logic.py
Synced 3 file(s)!
Adding file web/data/models.py
Synced 1 file(s)!
```
