"""
Centralized error handling and logging for Bangko ng Seton
"""
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import pytz

# Timezone configuration
PHILIPPINES_TZ = pytz.timezone('Asia/Manila')


class ErrorCode(Enum):
    """Standardized error codes"""
    # Configuration errors (1000-1099)
    CONFIG_MISSING_ENV = 1000
    CONFIG_INVALID_SHEETS_ID = 1001
    CONFIG_MISSING_CREDENTIALS = 1002
    CONFIG_INVALID_PORT = 1003
    
    # Google Sheets errors (1100-1199)
    SHEETS_CONNECTION_FAILED = 1100
    SHEETS_AUTH_FAILED = 1101
    SHEETS_WORKSHEET_NOT_FOUND = 1102
    SHEETS_QUOTA_EXCEEDED = 1103
    SHEETS_INVALID_SCHEMA = 1104
    
    # Card/Student errors (1200-1299)
    STUDENT_NOT_FOUND = 1200
    CARD_NOT_FOUND = 1201
    CARDS_NOT_LINKED = 1202
    CARD_INACTIVE = 1203
    DUPLICATE_CARD = 1204
    INVALID_CARD_UID = 1205
    
    # Balance/Transaction errors (1300-1399)
    INSUFFICIENT_BALANCE = 1300
    INVALID_AMOUNT = 1301
    TRANSACTION_FAILED = 1302
    BALANCE_UPDATE_FAILED = 1303
    
    # Serial/Arduino errors (1400-1499)
    SERIAL_PORT_NOT_FOUND = 1400
    SERIAL_CONNECTION_FAILED = 1401
    SERIAL_TIMEOUT = 1402
    ARDUINO_NOT_READY = 1403
    
    # Authentication errors (1500-1599)
    AUTH_INVALID_CREDENTIALS = 1500
    AUTH_SESSION_EXPIRED = 1501
    AUTH_UNAUTHORIZED = 1502
    
    # Generic errors (1900-1999)
    UNKNOWN_ERROR = 1900
    VALIDATION_ERROR = 1901
    OPERATION_TIMEOUT = 1902


class BankoError(Exception):
    """Base exception for Bangko ng Seton application"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now(PHILIPPINES_TZ)
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to JSON-serializable dictionary"""
        return {
            'error': {
                'code': self.error_code.value,
                'name': self.error_code.name,
                'message': self.message,
                'details': self.details,
                'recoverable': self.recoverable,
                'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        }


def setup_logging(log_dir: str = 'logs', log_level: str = 'INFO'):
    """
    Configure logging for the application
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Get current date for log filename
    today = datetime.now(PHILIPPINES_TZ).strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'bangko_{today}.log')
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Create logger
    logger = logging.getLogger('bangko')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler - writes to log file
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    logger.addHandler(file_handler)
    
    # Console handler - writes to stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = 'bangko') -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Log error with context information
    
    Args:
        error: Exception instance
        context: Additional context data
    """
    logger = get_logger()
    
    if isinstance(error, BankoError):
        logger.error(
            f"BankoError [{error.error_code.name}]: {error.message}",
            extra={
                'error_code': error.error_code.value,
                'details': error.details,
                'recoverable': error.recoverable,
                'context': context or {}
            }
        )
    else:
        logger.error(
            f"Unexpected error: {str(error)}",
            extra={'context': context or {}},
            exc_info=True
        )


def handle_sheets_error(error: Exception) -> BankoError:
    """
    Convert Google Sheets API errors to BankoError
    
    Args:
        error: Exception from gspread
    
    Returns:
        BankoError with appropriate code
    """
    error_str = str(error).lower()
    
    if 'worksheet not found' in error_str or 'invalid' in error_str:
        return BankoError(
            ErrorCode.SHEETS_WORKSHEET_NOT_FOUND,
            "Required worksheet not found in Google Sheets",
            {'original_error': str(error)},
            recoverable=False
        )
    elif 'quota' in error_str or 'rate limit' in error_str:
        return BankoError(
            ErrorCode.SHEETS_QUOTA_EXCEEDED,
            "Google Sheets API quota exceeded. Please wait and try again.",
            {'original_error': str(error)},
            recoverable=True
        )
    elif 'auth' in error_str or 'credentials' in error_str:
        return BankoError(
            ErrorCode.SHEETS_AUTH_FAILED,
            "Google Sheets authentication failed. Check credentials.json",
            {'original_error': str(error)},
            recoverable=False
        )
    else:
        return BankoError(
            ErrorCode.SHEETS_CONNECTION_FAILED,
            f"Failed to connect to Google Sheets: {str(error)}",
            {'original_error': str(error)},
            recoverable=True
        )


def handle_serial_error(error: Exception) -> BankoError:
    """
    Convert serial port errors to BankoError
    
    Args:
        error: Exception from pyserial
    
    Returns:
        BankoError with appropriate code
    """
    error_str = str(error).lower()
    
    if 'could not open port' in error_str or 'access is denied' in error_str:
        return BankoError(
            ErrorCode.SERIAL_PORT_NOT_FOUND,
            "Arduino serial port not found or in use by another program",
            {'original_error': str(error)},
            recoverable=True
        )
    elif 'timeout' in error_str:
        return BankoError(
            ErrorCode.SERIAL_TIMEOUT,
            "Arduino communication timeout. Check connection.",
            {'original_error': str(error)},
            recoverable=True
        )
    else:
        return BankoError(
            ErrorCode.SERIAL_CONNECTION_FAILED,
            f"Failed to connect to Arduino: {str(error)}",
            {'original_error': str(error)},
            recoverable=True
        )


def create_error_response(error: BankoError, status_code: int = 500) -> tuple:
    """
    Create Flask JSON error response
    
    Args:
        error: BankoError instance
        status_code: HTTP status code
    
    Returns:
        Tuple of (json_dict, status_code)
    """
    return error.to_dict(), status_code


# Common error messages
ERROR_MESSAGES = {
    ErrorCode.CONFIG_MISSING_ENV: "Required environment variable '{var}' is missing",
    ErrorCode.STUDENT_NOT_FOUND: "Student with ID '{student_id}' not found",
    ErrorCode.CARD_NOT_FOUND: "Card with UID '{card_uid}' not found",
    ErrorCode.CARDS_NOT_LINKED: "Money card '{money_card}' is not linked to ID card '{id_card}'",
    ErrorCode.INSUFFICIENT_BALANCE: "Insufficient balance. Current: ₱{balance}, Required: ₱{required}",
    ErrorCode.INVALID_AMOUNT: "Invalid amount: {amount}. Must be positive number.",
}
