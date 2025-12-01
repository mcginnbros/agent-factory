"""Logging configuration for AgentCore Factory.

This module provides structured logging with timestamps, log level configuration
from environment variables, and request ID tracking for debugging.
"""

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Optional

# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class RequestIdFilter(logging.Filter):
    """
    Logging filter that adds request ID to log records.
    
    This allows tracking related log messages across a request lifecycle.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to the log record."""
        record.request_id = request_id_var.get() or 'no-request-id'
        return True


class ColoredFormatter(logging.Formatter):
    """
    Colored log formatter for better readability in terminal.
    
    Uses ANSI color codes to highlight different log levels.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for next use
        record.levelname = levelname
        
        return formatted


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    use_colors: bool = True
) -> None:
    """
    Configure structured logging for the application.
    
    Sets up logging with:
    - Timestamps in ISO 8601 format
    - Log level from environment or parameter
    - Request ID tracking
    - Colored output (optional)
    - Structured format with module names
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  If None, reads from LOG_LEVEL environment variable.
                  Defaults to INFO if not set.
        log_format: Custom log format string. If None, uses default format.
        use_colors: Whether to use colored output (default: True)
        
    Example:
        >>> setup_logging(log_level='DEBUG')
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    # Determine log level
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Validate log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {log_level}, defaulting to INFO", file=sys.stderr)
        numeric_level = logging.INFO
        log_level = 'INFO'
    
    # Default log format with request ID
    if log_format is None:
        log_format = (
            '%(asctime)s | %(levelname)-8s | %(request_id)s | '
            '%(name)s:%(funcName)s:%(lineno)d | %(message)s'
        )
    
    # Create formatter
    if use_colors and sys.stdout.isatty():
        formatter = ColoredFormatter(
            log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    
    # Reduce noise from verbose libraries
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('docker').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request")
    """
    return logging.getLogger(name)


def log_with_request_id(func):
    """
    Decorator to add request ID tracking to a function.
    
    Generates a unique request ID for each function invocation and
    adds it to all log messages within that function's execution.
    
    Args:
        func: Function to decorate
        
    Returns:
        Wrapped function with request ID tracking
        
    Example:
        >>> @log_with_request_id
        ... def process_request(data):
        ...     logger.info("Processing data")
        ...     return result
    """
    def wrapper(*args, **kwargs):
        # Generate unique request ID
        req_id = str(uuid.uuid4())[:8]
        
        # Set request ID in context
        token = request_id_var.set(req_id)
        
        try:
            # Execute function
            return func(*args, **kwargs)
        finally:
            # Reset request ID
            request_id_var.reset(token)
    
    return wrapper


def set_request_id(request_id: str) -> None:
    """
    Manually set the request ID for the current context.
    
    Useful when you want to use a specific request ID (e.g., from an API request).
    
    Args:
        request_id: Request ID to set
        
    Example:
        >>> set_request_id("req-12345")
        >>> logger.info("This log will include req-12345")
    """
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.
    
    Returns:
        Current request ID or None if not set
        
    Example:
        >>> req_id = get_request_id()
        >>> print(f"Current request: {req_id}")
    """
    return request_id_var.get()


def generate_request_id() -> str:
    """
    Generate a new unique request ID.
    
    Returns:
        New request ID (8-character UUID)
        
    Example:
        >>> req_id = generate_request_id()
        >>> set_request_id(req_id)
    """
    return str(uuid.uuid4())[:8]


class LogContext:
    """
    Context manager for scoped request ID tracking.
    
    Automatically generates and sets a request ID for the duration
    of the context, then resets it when exiting.
    
    Example:
        >>> with LogContext():
        ...     logger.info("This has a request ID")
        ...     do_work()
        >>> logger.info("This has a different request ID")
    """
    
    def __init__(self, request_id: Optional[str] = None):
        """
        Initialize log context.
        
        Args:
            request_id: Optional request ID to use. If None, generates a new one.
        """
        self.request_id = request_id or generate_request_id()
        self.token = None
    
    def __enter__(self):
        """Enter context and set request ID."""
        self.token = request_id_var.set(self.request_id)
        return self.request_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset request ID."""
        if self.token:
            request_id_var.reset(self.token)


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function entry and exit with timing.
    
    Args:
        logger: Logger instance to use
        
    Returns:
        Decorator function
        
    Example:
        >>> logger = get_logger(__name__)
        >>> @log_function_call(logger)
        ... def my_function(arg1, arg2):
        ...     return arg1 + arg2
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Entering {func_name}")
            
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Exiting {func_name} (duration: {duration:.3f}s)")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"Exception in {func_name} after {duration:.3f}s: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


# Initialize logging on module import with default settings
# This ensures logging is available even if setup_logging() is not called
if not logging.getLogger().handlers:
    setup_logging()
