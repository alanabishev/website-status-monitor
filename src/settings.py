import os

# settings.py


class DatabaseSettings:
    """Database configuration settings."""

    HOST = os.getenv("DATABASE_HOST", "localhost")
    PORT = os.getenv("DATABASE_PORT", 5432)
    NAME = os.getenv("DATABASE_NAME", "postgres")
    USER = os.getenv("DATABASE_USER", "postgres")
    PASSWORD = os.getenv("DATABASE_PASSWORD", "password")


class MonitoringSettings:
    """Website monitoring settings."""

    UVICORN_PORT = os.getenv("UVICORN_PORT", 8000)

    # Timeout in seconds for each website request.
    REQUEST_TIMEOUT = 30
    # Worker wait time in seconds before fetching next batch of monitoring results.
    RESULTS_WORKER_WAIT_TIME = 3
    # Maximum number of monitoring results to save in one batch.
    RESULTS_BATCH_SAVE_SIZE = 100
