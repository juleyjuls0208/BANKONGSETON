# gunicorn config — Web Dashboard (eventlet worker for SocketIO, single process)
bind = "127.0.0.1:5000"
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
graceful_timeout = 30
pythonpath = "/opt/bankongseton/backend/dashboard:/opt/bankongseton/backend"
chdir = "/opt/bankongseton/backend/dashboard"
accesslog = "/var/log/bankongseton/web.access.log"
errorlog = "/var/log/bankongseton/web.error.log"
loglevel = "info"
