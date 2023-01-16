from multiprocessing import cpu_count


# Socket Path

bind = 'unix:/home/ubuntu/socket/bet4live.sock'


# Worker Options

workers = cpu_count() + 1

worker_class = 'uvicorn.workers.UvicornH11Worker'

GUNICORN_CMD_ARGS = "--keep-alive 0"

# Logging Options

loglevel = 'debug'

accesslog = '/home/ubuntu/logs/live_access.log'

errorlog = '/home/ubuntu/logs/live_error.log'
