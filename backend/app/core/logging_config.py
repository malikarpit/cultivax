"""
Structured Logging Configuration

Configures Python's built-in logging to output JSON-formatted strings,
allowing easy ingestion into ELK, Datadog, or Google Cloud Logging.
"""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON objects.
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.default_kwargs = kwargs

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            **self.default_kwargs
        }

        # Add correlation ID if present in the record attributes
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id

        # Add exception details if present
        if record.exc_info:
            log_obj["exception"] = "".join(traceback.format_exception(*record.exc_info))

        return json.dumps(log_obj)

def setup_structured_logging(app_name: str, environment: str = "development", log_level: int = logging.INFO):
    """
    Initializes root logger to use JSON formatting.
    """
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicate logs if run multiple times
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = JSONFormatter(app=app_name, env=environment)
    handler.setFormatter(formatter)
    
    root_logger.addHandler(handler)

    # Prevent uvicorn access logs from duplicating or looking messy.
    # Optionally re-format uvicorn access logs.
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = []
    uvicorn_access_logger.propagate = True
    
    # Do the same for general uvicorn
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []
    uvicorn_logger.propagate = True

    return root_logger
