# gunicorn config — Loading Kiosk (eventlet worker for SocketIO, single process)
bind = "127.0.0.1:5002"
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
graceful_timeout = 30
pythonpath = "/opt/bankongseton/backend/kiosk:/opt/bankongseton/backend:/opt/bankongseton/backend/dashboard"
chdir = "/opt/bankongseton/backend/kiosk"
accesslog = "/var/log/bankongseton/kiosk.access.log"
errorlog = "/var/log/bankongseton/kiosk.error.log"
loglevel = "info"
