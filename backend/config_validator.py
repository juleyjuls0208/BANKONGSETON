"""
Configuration validation and startup checks for Bangko ng Seton
"""
import os
import sys
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import serial.tools.list_ports

# Load environment variables
load_dotenv()

# Import error handling
try:
    from backend.errors import BankoError, ErrorCode, get_logger, setup_logging
except ImportError:
    from errors import BankoError, ErrorCode, get_logger, setup_logging


class ValidationResult:
    """Result of validation check"""
    
    def __init__(self, passed: bool, message: str, details: Optional[Dict] = None):
        self.passed = passed
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        status = "✓" if self.passed else "✗"
        return f"{status} {self.message}"


class ConfigValidator:
    """Validates application configuration and environment"""
    
    def __init__(self):
        self.logger = None
        self.results: List[ValidationResult] = []
        self.critical_failures = []
    
    def validate_all(self, log_level: str = 'INFO') -> bool:
        """
        Run all validation checks
        
        Returns:
            True if all checks passed, False otherwise
        """
        # Setup logging first
        self.logger = setup_logging(log_level=log_level)
        self.logger.info("=" * 60)
        self.logger.info("Bangko ng Seton - Startup Validation")
        self.logger.info("=" * 60)
        
        # Run all checks
        self._validate_environment_variables()
        self._validate_credentials_file()
        self._validate_google_sheets_connection()
        self._validate_google_sheets_schema()
        self._validate_serial_ports()
        
        # Print results
        self._print_results()
        
        # Return overall status
        return len(self.critical_failures) == 0
    
    def _validate_environment_variables(self):
        """Validate required environment variables"""
        self.logger.info("\n1. Checking environment variables...")
        
        required_vars = {
            'GOOGLE_SHEETS_ID': 'Google Sheets spreadsheet ID',
            'FLASK_SECRET_KEY': 'Flask secret key for sessions',
        }
        
        optional_vars = {
            'ADMIN_USERNAME': 'Admin login username',
            'ADMIN_PASSWORD': 'Admin login password',
            'FINANCE_USERNAME': 'Finance login username',
            'FINANCE_PASSWORD': 'Finance login password',
            'SERIAL_PORT': 'Cashier Arduino serial port',
            'ADMIN_PORT': 'Admin Arduino serial port',
            'BAUD_RATE': 'Serial communication baud rate',
        }
        
        # Check required variables
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                self.results.append(ValidationResult(
                    True,
                    f"{var}: {description}",
                    {'value': value[:20] + '...' if len(value) > 20 else value}
                ))
            else:
                result = ValidationResult(
                    False,
                    f"{var}: MISSING - {description}",
                    {'required': True}
                )
                self.results.append(result)
                self.critical_failures.append(result)
        
        # Check optional variables (warnings only)
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                self.results.append(ValidationResult(
                    True,
                    f"{var}: {description}",
                    {'value': value}
                ))
            else:
                self.results.append(ValidationResult(
                    False,
                    f"{var}: Not set (optional) - {description}",
                    {'required': False}
                ))
    
    def _validate_credentials_file(self):
        """Validate Google Sheets credentials file exists"""
        self.logger.info("\n2. Checking credentials file...")
        
        # Check multiple possible locations
        possible_paths = [
            'config/credentials.json',
            'credentials.json',
            '../config/credentials.json',
            '../../config/credentials.json'
        ]
        
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                self.results.append(ValidationResult(
                    True,
                    f"Credentials file found: {path}",
                    {'path': os.path.abspath(path)}
                ))
                found = True
                break
        
        if not found:
            result = ValidationResult(
                False,
                "Credentials file NOT FOUND. Checked: " + ", ".join(possible_paths),
                {'required': True}
            )
            self.results.append(result)
            self.critical_failures.append(result)
    
    def _validate_google_sheets_connection(self):
        """Validate connection to Google Sheets"""
        self.logger.info("\n3. Testing Google Sheets connection...")
        
        try:
            # Try to connect
            credentials_path = self._find_credentials_path()
            if not credentials_path:
                result = ValidationResult(
                    False,
                    "Cannot test connection - credentials file not found",
                    {'required': True}
                )
                self.results.append(result)
                return
            
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
            client = gspread.authorize(creds)
            
            sheets_id = os.getenv('GOOGLE_SHEETS_ID')
            if not sheets_id:
                result = ValidationResult(
                    False,
                    "Cannot test connection - GOOGLE_SHEETS_ID not set",
                    {'required': True}
                )
                self.results.append(result)
                self.critical_failures.append(result)
                return
            
            # Try to open spreadsheet
            spreadsheet = client.open_by_key(sheets_id)
            
            self.results.append(ValidationResult(
                True,
                f"Connected to Google Sheets: {spreadsheet.title}",
                {
                    'spreadsheet_id': sheets_id,
                    'title': spreadsheet.title,
                    'url': spreadsheet.url
                }
            ))
            
        except Exception as e:
            result = ValidationResult(
                False,
                f"Failed to connect to Google Sheets: {str(e)}",
                {'error': str(e), 'required': True}
            )
            self.results.append(result)
            self.critical_failures.append(result)
    
    def _validate_google_sheets_schema(self):
        """Validate Google Sheets has required sheets and columns"""
        self.logger.info("\n4. Validating Google Sheets schema...")
        
        try:
            credentials_path = self._find_credentials_path()
            if not credentials_path:
                return
            
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
            client = gspread.authorize(creds)
            spreadsheet = client.open_by_key(os.getenv('GOOGLE_SHEETS_ID'))
            
            # Required sheets and their columns
            required_schema = {
                'Users': ['StudentID', 'Name', 'IDCardNumber', 'MoneyCardNumber', 
                         'Status', 'ParentEmail', 'DateRegistered'],
                'Money Accounts': ['MoneyCardNumber', 'LinkedIDCard', 'Balance', 
                                  'Status', 'LastUpdated', 'TotalLoaded'],
                'Transactions Log': ['TransactionID', 'Timestamp', 'StudentID', 
                                    'MoneyCardNumber', 'TransactionType', 'Amount', 
                                    'BalanceBefore', 'BalanceAfter', 'Status', 'ErrorMessage'],
                'Lost Card Reports': ['ReportID', 'ReportDate', 'StudentID', 
                                     'OldCardNumber', 'NewCardNumber', 'TransferredBalance', 
                                     'ReportedBy', 'Status']
            }
            
            for sheet_name, expected_columns in required_schema.items():
                try:
                    worksheet = spreadsheet.worksheet(sheet_name)
                    actual_columns = worksheet.row_values(1)
                    
                    # Check if all expected columns exist
                    missing = [col for col in expected_columns if col not in actual_columns]
                    
                    if not missing:
                        self.results.append(ValidationResult(
                            True,
                            f"Sheet '{sheet_name}' has correct schema ({len(actual_columns)} columns)",
                            {'columns': actual_columns}
                        ))
                    else:
                        result = ValidationResult(
                            False,
                            f"Sheet '{sheet_name}' missing columns: {', '.join(missing)}",
                            {
                                'missing_columns': missing,
                                'expected': expected_columns,
                                'actual': actual_columns,
                                'required': True
                            }
                        )
                        self.results.append(result)
                        self.critical_failures.append(result)
                
                except gspread.exceptions.WorksheetNotFound:
                    result = ValidationResult(
                        False,
                        f"Sheet '{sheet_name}' NOT FOUND",
                        {'required': True}
                    )
                    self.results.append(result)
                    self.critical_failures.append(result)
        
        except Exception as e:
            self.logger.warning(f"Could not validate schema: {str(e)}")
    
    def _validate_serial_ports(self):
        """Validate Arduino serial ports if configured"""
        self.logger.info("\n5. Checking Arduino serial ports...")
        
        # List available ports
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        if available_ports:
            self.results.append(ValidationResult(
                True,
                f"Found {len(available_ports)} serial port(s): {', '.join(available_ports)}",
                {'ports': available_ports}
            ))
        else:
            self.results.append(ValidationResult(
                False,
                "No serial ports found (Arduino may not be connected)",
                {'required': False}
            ))
        
        # Check configured ports
        for var in ['SERIAL_PORT', 'ADMIN_PORT']:
            port = os.getenv(var)
            if port:
                if port in available_ports:
                    self.results.append(ValidationResult(
                        True,
                        f"{var} ({port}) is available",
                        {'port': port}
                    ))
                else:
                    self.results.append(ValidationResult(
                        False,
                        f"{var} ({port}) NOT FOUND in available ports",
                        {'required': False, 'port': port}
                    ))
    
    def _find_credentials_path(self) -> Optional[str]:
        """Find credentials.json file"""
        possible_paths = [
            'config/credentials.json',
            'credentials.json',
            '../config/credentials.json',
            '../../config/credentials.json'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _print_results(self):
        """Print validation results"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("VALIDATION RESULTS")
        self.logger.info("=" * 60)
        
        passed = 0
        failed = 0
        warnings = 0
        
        for result in self.results:
            if result.passed:
                self.logger.info(f"✓ {result.message}")
                passed += 1
            else:
                if result.details.get('required', False):
                    self.logger.error(f"✗ {result.message}")
                    failed += 1
                else:
                    self.logger.warning(f"⚠ {result.message}")
                    warnings += 1
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"SUMMARY: {passed} passed, {failed} failed, {warnings} warnings")
        self.logger.info("=" * 60)
        
        if self.critical_failures:
            self.logger.error("\nCRITICAL: The following issues must be fixed:")
            for failure in self.critical_failures:
                self.logger.error(f"  - {failure.message}")
            self.logger.error("\nApplication cannot start safely. Please fix these issues.")
            return False
        else:
            if warnings > 0:
                self.logger.warning("\nApplication can start, but some features may not work.")
            else:
                self.logger.info("\n✓ All checks passed! Application is ready to start.")
            return True


def validate_config(exit_on_failure: bool = False) -> bool:
    """
    Convenience function to validate configuration
    
    Args:
        exit_on_failure: If True, sys.exit(1) on validation failure
    
    Returns:
        True if validation passed
    """
    validator = ConfigValidator()
    passed = validator.validate_all()
    
    if not passed and exit_on_failure:
        sys.exit(1)
    
    return passed


if __name__ == '__main__':
    # Run validation when script is executed directly
    validate_config(exit_on_failure=True)
