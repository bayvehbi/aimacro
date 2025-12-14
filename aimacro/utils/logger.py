"""
Logging utility for verbose mode.
Provides functions to log messages conditionally based on verbose mode setting.
"""
import sys


class Logger:
    """Simple logger that respects verbose mode setting."""
    
    def __init__(self, verbose=False):
        """
        Initialize logger.
        
        Args:
            verbose: If True, verbose messages will be printed. Default: False
        """
        self.verbose = verbose
    
    def set_verbose(self, verbose):
        """Update verbose mode."""
        self.verbose = verbose
    
    def info(self, message):
        """Print informational message (always shown)."""
        print(message)
    
    def verbose_msg(self, message):
        """Print verbose/debug message (only if verbose mode is enabled)."""
        if self.verbose:
            print(f"[VERBOSE] {message}")
    
    def debug(self, message):
        """Alias for verbose_msg (for consistency)."""
        self.verbose_msg(message)
    
    def error(self, message):
        """Print error message (always shown)."""
        print(f"[ERROR] {message}")


# Global logger instance (will be initialized with settings)
_logger = None


def init_logger(verbose=False):
    """Initialize the global logger with verbose mode."""
    global _logger
    _logger = Logger(verbose)


def get_logger():
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = Logger(verbose=False)
    return _logger


def info(message):
    """Print informational message (always shown)."""
    get_logger().info(message)


def verbose(message):
    """Print verbose/debug message (only if verbose mode is enabled)."""
    get_logger().verbose_msg(message)


def debug(message):
    """Alias for verbose (for consistency)."""
    get_logger().debug(message)


def error(message):
    """Print error message (always shown)."""
    get_logger().error(message)

