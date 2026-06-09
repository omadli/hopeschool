"""Gunicorn configuration for Hope School (production).

Loaded by the systemd unit:
    gunicorn --config deploy/gunicorn.conf.py config.wsgi:application

Access/error logs go to stdout/stderr, which systemd captures in the journal
(``journalctl -u hopeschool``). Tune workers via the GUNICORN_WORKERS env var —
the SQLite backend prefers a small pool to avoid write contention, so the
default is intentionally modest rather than the (2*CPU)+1 rule of thumb.
"""
import os

# Bind to a unix socket in the systemd RuntimeDirectory (/run/hopeschool).
# nginx (www-data) reads it; see hopeschool.service Group=www-data + umask below.
bind = os.environ.get("GUNICORN_BIND", "unix:/run/hopeschool/gunicorn.sock")

workers = int(os.environ.get("GUNICORN_WORKERS", "3"))
worker_class = "sync"

# Socket created mode 0660 so the www-data nginx worker can read/write it.
umask = 0o007

timeout = 60
graceful_timeout = 30
keepalive = 5

# Recycle workers periodically to bound memory growth (Pillow/thumbnails).
max_requests = 1000
max_requests_jitter = 100

# "-" → stdout/stderr → journald.
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")

proc_name = "hopeschool"
