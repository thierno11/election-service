import logging
import json
from datetime import datetime
from typing import Any, Dict
import os

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        for attr in ["request_id", "user_id", "method", "url", "client_host", "user_agent", "status_code", "process_time"]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        os.makedirs("logs", exist_ok=True)

        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger