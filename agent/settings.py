import json
import ipaddress
from typing import Any, Dict


class Settings:
    """
    Class for managing application settings with validation
    """

    # Default values
    DEFAULT_SETTINGS = {
        'server_address': '127.0.0.1',
        'server_port': 8080,
        'timeout_scan': 3600,
        'timeout_send': 3600
    }

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize settings manager

        Args:
            config_file (str): Path to configuration file
        """
        self.config_file = config_file
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.load()

    def load(self) -> None:
        """
        Load settings from JSON file
        If file doesn't exist or has errors, use default values
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_settings = json.load(f)

            # Validate and update each setting
            for key, value in file_settings.items():
                if key in self.DEFAULT_SETTINGS:
                    try:
                        # Use setter for validation
                        setattr(self, key, value)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid value for {key}: {value}. Using default: {self.DEFAULT_SETTINGS[key]}")
                        self._settings[key] = self.DEFAULT_SETTINGS[key]
                else:
                    print(f"Warning: Unknown setting '{key}' in config file")

        except FileNotFoundError:
            print(f"Config file '{self.config_file}' not found. Using default settings.")
            self.save()  # Create config file with default values
        except json.JSONDecodeError as e:
            print(f"Error parsing config file: {e}. Using default settings.")
        except Exception as e:
            print(f"Error loading settings: {e}. Using default settings.")

    def save(self) -> None:
        """
        Save current settings to JSON file
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
            print(f"Settings saved to '{self.config_file}'")
        except Exception as e:
            print(f"Error saving settings: {e}")

    # Validation methods
    def _validate_server_address(self, value: Any) -> str:
        """Validate server IP address"""
        if not isinstance(value, str):
            raise ValueError(f"Server address must be a string, got {type(value)}")

        try:
            ipaddress.ip_address(value)
            return value
        except ValueError:
            raise ValueError(f"Invalid IP address: {value}")

    def _validate_unsigned_int(self, value: Any, field_name: str, allow_numeric_string: bool = False) -> int:
        """Validate unsigned integer"""
        if allow_numeric_string and isinstance(value, str):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValueError(f"{field_name} must be an integer, got string: '{value}'")

        if not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer, got {type(value)}")

        if value < 0:
            raise ValueError(f"{field_name} must be non-negative, got {value}")

        return value

    # Property getters and setters
    @property
    def server_address(self) -> str:
        """Get server address"""
        return self._settings['server_address']

    @server_address.setter
    def server_address(self, value: str) -> None:
        """Set server address with validation"""
        self._settings['server_address'] = self._validate_server_address(value)

    @property
    def server_port(self) -> int:
        """Get server port"""
        return self._settings['server_port']

    @server_port.setter
    def server_port(self, value: int) -> None:
        """Set server port with validation"""
        # For port, we don't allow numeric strings - must be actual int
        validated_value = self._validate_unsigned_int(value, "Server port", allow_numeric_string=False)

        # Additional validation for port range
        if validated_value > 65535:
            raise ValueError(f"Server port must be between 0 and 65535, got {validated_value}")

        self._settings['server_port'] = validated_value

    @property
    def timeout_scan(self) -> int:
        """Get scan timeout"""
        return self._settings['timeout_scan']

    @timeout_scan.setter
    def timeout_scan(self, value: int) -> None:
        """Set scan timeout with validation"""
        # For timeouts, we allow numeric strings during loading but not during direct assignment
        allow_strings = False  # Don't allow strings in direct assignment
        self._settings['timeout_scan'] = self._validate_unsigned_int(value, "Scan timeout", allow_numeric_string=allow_strings)

    @property
    def timeout_send(self) -> int:
        """Get send timeout"""
        return self._settings['timeout_send']

    @timeout_send.setter
    def timeout_send(self, value: int) -> None:
        """Set send timeout with validation"""
        # For timeouts, we allow numeric strings during loading but not during direct assignment
        allow_strings = False  # Don't allow strings in direct assignment
        self._settings['timeout_send'] = self._validate_unsigned_int(value, "Send timeout",  allow_numeric_string=allow_strings)

    # Additional methods
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return self._settings.copy()

    def update(self, **kwargs) -> None:
        """
        Update multiple settings at once

        Args:
            **kwargs: Setting names and values
        """
        errors = []
        for key, value in kwargs.items():
            if key in self.DEFAULT_SETTINGS:
                try:
                    setattr(self, key, value)
                except (ValueError, TypeError) as e:
                    errors.append(f"{key}: {e}")
            else:
                errors.append(f"Unknown setting: {key}")

        if errors:
            raise ValueError("; ".join(errors))

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values"""
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.save()

    def __str__(self) -> str:
        """String representation of settings"""
        settings_str = []
        for key, value in self._settings.items():
            settings_str.append(f"{key}: {value}")
        return "\n".join(settings_str)

    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"Settings(config_file='{self.config_file}', settings={self._settings})"
