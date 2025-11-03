"""
Error handling and retry logic for data collection
"""

from typing import Callable, Any, Optional, Dict
from datetime import datetime, timedelta
import time
from app.core.logging import get_logger

logger = get_logger(__name__)


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (Exception,)
    ):
        """
        Initialize retry configuration
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before retry
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            retryable_exceptions: Tuple of exceptions that should trigger retry
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions


def retry_with_backoff(
    func: Callable,
    retry_config: Optional[RetryConfig] = None,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Execute function with exponential backoff retry logic
    
    Args:
        func: Function to execute
        retry_config: Retry configuration (uses default if None)
        context: Additional context for logging
    
    Returns:
        Result from function execution
    
    Raises:
        Last exception if all retries fail
    """
    config = retry_config or RetryConfig()
    context = context or {}
    
    last_exception = None
    delay = config.initial_delay
    
    for attempt in range(config.max_retries + 1):
        try:
            result = func()
            if attempt > 0:
                logger.info(f"Function succeeded after {attempt} retries", 
                           **context)
            return result
            
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_retries:
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_retries + 1} failed, "
                    f"retrying in {delay:.2f}s",
                    error=str(e),
                    **context
                )
                time.sleep(delay)
                
                # Exponential backoff
                delay = min(delay * config.exponential_base, config.max_delay)
            else:
                logger.error(
                    f"All {config.max_retries + 1} attempts failed",
                    error=str(e),
                    **context
                )
                raise
    
    # Should not reach here, but handle just in case
    if last_exception:
        raise last_exception
    raise Exception("Unexpected error in retry logic")


class ErrorHandler:
    """Handles errors and exceptions in data collection"""
    
    def __init__(self):
        """Initialize error handler"""
        self.error_log: list = []
    
    def handle_error(
        self,
        error: Exception,
        source: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an error and return error information
        
        Args:
            error: Exception that occurred
            source: Name of data source where error occurred
            context: Additional context information
        
        Returns:
            Dictionary with error information
        """
        error_info = {
            "source": source,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }
        
        # Log error
        logger.error(
            f"Error in data source '{source}'",
            error_type=error_info["error_type"],
            error_message=error_info["error_message"],
            **context or {}
        )
        
        # Store in error log
        self.error_log.append(error_info)
        
        return error_info
    
    def get_error_summary(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of errors
        
        Args:
            source: Optional source name to filter by
        
        Returns:
            Dictionary with error summary
        """
        errors = self.error_log
        
        if source:
            errors = [e for e in errors if e.get("source") == source]
        
        error_types = {}
        for error in errors:
            error_type = error.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(errors),
            "by_source": {e["source"]: sum(1 for err in errors if err["source"] == e["source"]) 
                         for e in errors},
            "by_type": error_types,
            "recent_errors": errors[-10:]  # Last 10 errors
        }


def safe_execute(
    func: Callable,
    default_return: Any = None,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Safely execute a function, returning default value on error
    
    Args:
        func: Function to execute
        default_return: Value to return on error
        context: Additional context for logging
    
    Returns:
        Function result or default_return
    """
    try:
        return func()
    except Exception as e:
        logger.error(f"Safe execution failed", error=str(e), **(context or {}))
        return default_return

