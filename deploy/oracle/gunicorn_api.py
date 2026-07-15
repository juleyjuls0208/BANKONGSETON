# gunicorn config — API (sync worker, single process, mandatory)
bind = "127.0.0.1:5001"
workers = 1
worker_class = "sync"
threads = 4
timeout = 120
graceful_timeout = 30
pythonpath = "/opt/bankongseton/backend/api:/opt/bankongseton/backend"
chdir = "/opt/bankongseton/backend/api"
accesslog = "/var/log/bankongseton/api.access.log"
errorlog = "/var/log/bankongseton/api.error.log"
loglevel = "info"
