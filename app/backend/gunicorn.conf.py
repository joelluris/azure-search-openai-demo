import multiprocessing
import os

max_requests = 1000
max_requests_jitter = 50
log_file = "-"
bind = "0.0.0.0"

timeout = 600  # Increased for initial startup
workers = 2  # Simple: just 2 workers
worker_class = "uvicorn.workers.UvicornWorker"  # Standard uvicorn worker
