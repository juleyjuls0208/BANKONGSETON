# gunicorn config — Card Registration Panel (on-prem; eventlet worker for SocketIO)
# Runs ONLY where a USB Arduino RFID reader is attached. Not deployed to the
# public cloud dashboard. Served under /panel/ via nginx.
bind = "127.0.0.1:5005"
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
graceful_timeout = 30
pythonpath = "/opt/bankongseton/backend/dashboard:/opt/bankongseton/backend"
chdir = "/opt/bankongseton/backend/dashboard"
accesslog = "/var/log/bankongseton/registration.access.log"
errorlog = "/var/log/bankongseton/registration.error.log"
loglevel = "info"
