"""Gunicorn configuration for the Docker image.

Every value can be overridden with an environment variable so the same image
works across environments.
"""
import os

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# SQLite serialises writes, so a small worker pool is deliberate.
workers = int(os.getenv("GUNICORN_WORKERS", "3"))
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Gunicorn 26 defaults this to $PWD/.gunicorn, which the non-root user cannot
# create in /app. /tmp is writable and does not need to survive restarts.
control_socket = os.getenv("GUNICORN_CONTROL_SOCKET", "/tmp/gunicorn.ctl")

# Log the resolved worker count on startup; helpful when tuning on a small host.
print(f"[gunicorn] workers={workers} threads={threads} timeout={timeout}s")
