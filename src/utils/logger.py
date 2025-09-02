#!/usr/bin/env python3
"""
RepoReadme - Enhanced Logging System

Provides comprehensive logging functionality for the RepoReadme application
with support for different log levels, file rotation, and structured output.

Based on GitGuard's logging architecture but adapted for README generation tasks.
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import json

class RepoReadmeLogger:
    """Enhanced logger for RepoReadme operations."""
    
    def __init__(self, log_level: str = "INFO", log_to_file: bool = True, log_to_console: bool = True):
        """Initialize the logger with specified configuration."""
        self.log_level = log_level.upper()
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        
        # Create logs directory
        self.log_dir = Path.home() / ".reporeadme" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup log files
        self.main_log_file = self.log_dir / "reporeadme.log"
        self.session_log_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Initialize logging
        self._setup_logging()
        
        # Log startup
        self.log_application_start()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logger
        self.logger = logging.getLogger('reporeadme')
        self.logger.setLevel(getattr(logging, self.log_level))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.log_level))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handlers
        if self.log_to_file:
            # Main log file
            file_handler = logging.FileHandler(self.main_log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(getattr(logging, self.log_level))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Session log file
            session_handler = logging.FileHandler(self.session_log_file, mode='w', encoding='utf-8')
            session_handler.setLevel(getattr(logging, self.log_level))
            session_handler.setFormatter(formatter)
            self.logger.addHandler(session_handler)
    
    def log_application_start(self):
        """Log application startup information."""
        self.info("=" * 60, "APP")
        self.info("RepoReadme - Automatic README Generator Starting", "APP")
        self.info(f"Session log: {self.session_log_file}", "APP")
        self.info(f"Log level: {self.log_level}", "APP")
        self.info(f"Python version: {sys.version}", "APP")
        self.info("=" * 60, "APP")
    
    def debug(self, message: str, category: str = "DEBUG"):
        """Log debug message."""
        self.logger.debug(f"[{category}] {message}")
    
    def info(self, message: str, category: str = "INFO"):
        """Log info message."""
        self.logger.info(f"[{category}] {message}")
    
    def warning(self, message: str, category: str = "WARN"):
        """Log warning message."""
        self.logger.warning(f"[{category}] {message}")
    
    def error(self, message: str, category: str = "ERROR", exception: Exception = None):
        """Log error message with optional exception details."""
        self.logger.error(f"[{category}] {message}")
        if exception:
            self.logger.error(f"[{category}] Exception details: {type(exception).__name__}: {str(exception)}")
    
    def critical(self, message: str, category: str = "CRITICAL"):
        """Log critical message."""
        self.logger.critical(f"[{category}] {message}")
    
    def log_repository_analysis(self, repo_name: str, analysis_type: str, status: str, details: str = ""):
        """Log repository analysis activity."""
        message = f"Repository: {repo_name} | Type: {analysis_type} | Status: {status}"
        if details:
            message += f" | Details: {details}"
        self.info(message, "ANALYSIS")
    
    def log_readme_generation(self, repo_name: str, template: str, output_path: str, success: bool):
        """Log README generation activity."""
        status = "SUCCESS" if success else "FAILED"
        message = f"Generated README for {repo_name} | Template: {template} | Output: {output_path} | Status: {status}"
        self.info(message, "GENERATION")
    
    def log_performance(self, operation: str, duration_ms: float, details: Dict[str, Any] = None):
        """Log performance metrics."""
        message = f"Operation: {operation} | Duration: {duration_ms:.2f}ms"
        if details:
            message += f" | Details: {json.dumps(details, default=str)}"
        self.info(message, "PERF")
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """Log error with detailed context information."""
        self.error(f"Error occurred: {type(error).__name__}: {str(error)}", "ERROR")
        self.error(f"Context: {json.dumps(context, default=str, indent=2)}", "ERROR")
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            removed_count = 0
            
            for log_file in self.log_dir.glob("session_*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                self.info(f"Cleaned up {removed_count} old log files", "CLEANUP")
                
        except Exception as e:
            self.error(f"Failed to cleanup old logs: {e}", "CLEANUP")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        try:
            stats = {
                "log_directory": str(self.log_dir),
                "main_log_size": self.main_log_file.stat().st_size if self.main_log_file.exists() else 0,
                "session_log_size": self.session_log_file.stat().st_size if self.session_log_file.exists() else 0,
                "total_log_files": len(list(self.log_dir.glob("*.log"))),
                "log_level": self.log_level
            }
            return stats
        except Exception as e:
            self.error(f"Failed to get log stats: {e}", "STATS")
            return {}


# Global logger instance
_logger_instance: Optional[RepoReadmeLogger] = None

def get_logger(log_level: str = "INFO", log_to_file: bool = True, log_to_console: bool = True) -> RepoReadmeLogger:
    """Get or create the global logger instance."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = RepoReadmeLogger(
            log_level=log_level,
            log_to_file=log_to_file, 
            log_to_console=log_to_console
        )
    
    return _logger_instance

def set_log_level(level: str):
    """Set the global log level."""
    logger = get_logger()
    logger.log_level = level.upper()
    logger._setup_logging()