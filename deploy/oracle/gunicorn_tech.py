# gunicorn config — Tech/Admin Kiosk (eventlet worker for SocketIO, single process)
bind = "127.0.0.1:5004"
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
graceful_timeout = 30
pythonpath = "/opt/bankongseton/backend/tech:/opt/bankongseton/backend:/opt/bankongseton/backend/dashboard"
chdir = "/opt/bankongseton/backend/tech"
accesslog = "/var/log/bankongseton/tech.access.log"
errorlog = "/var/log/bankongseton/tech.error.log"
loglevel = "info"
