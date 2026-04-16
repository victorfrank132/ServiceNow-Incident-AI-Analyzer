"""Logging configuration for the incident agent."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "incident_id"):
            log_data["incident_id"] = record.incident_id

        if hasattr(record, "action"):
            log_data["action"] = record.action

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("incident_agent")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with JSON formatting
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        json_formatter = JSONFormatter()
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance."""
    return logging.getLogger(name)


def setup_llm_analysis_logging(log_file: str = "logs/llm_analysis.log") -> logging.Logger:
    """
    Set up dedicated logging for LLM analysis (input/output messages).

    Args:
        log_file: File path for LLM analysis logs

    Returns:
        Configured LLM analysis logger
    """
    logger = logging.getLogger("llm_analysis")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        for handler in logger.handlers:
            handler.close()
        logger.handlers = []

    # File handler with JSON formatting
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)
    
    # Custom formatter for LLM analysis with detailed context
    class LLMAnalysisFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "incident_number": getattr(record, "incident_number", ""),
                "message": record.getMessage(),
            }
            
            if hasattr(record, "llm_input"):
                log_data["llm_input"] = record.llm_input
            
            if hasattr(record, "llm_output"):
                log_data["llm_output"] = record.llm_output
            
            if hasattr(record, "reasoning"):
                reasoning = getattr(record, "reasoning", None)
                if reasoning:
                    log_data["reasoning"] = reasoning
            
            if hasattr(record, "confidence"):
                log_data["confidence"] = record.confidence
            
            if hasattr(record, "tokens_used"):
                log_data["tokens_used"] = record.tokens_used
            
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_data)
    
    json_formatter = LLMAnalysisFormatter()
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)

    return logger
