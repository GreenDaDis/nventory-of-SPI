import unittest
import json
import tempfile
import os
from agent.settings import Settings


class TestSettings(unittest.TestCase):
    """Test cases for Settings class"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "test_config.json")

    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def create_test_config(self, config_data):
        """Helper method to create test config file"""
        with open(self.test_config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)

    def test_default_values(self):
        """Test that default values are set correctly"""
        settings = Settings(self.test_config_file)

        self.assertEqual(settings.server_address, "127.0.0.1")
        self.assertEqual(settings.server_port, 8080)
        self.assertEqual(settings.timeout_scan, 3600)
        self.assertEqual(settings.timeout_send, 300)

    def test_load_valid_config(self):
        """Test loading valid configuration file"""
        config_data = {
            "server_address": "192.168.1.100",
            "server_port": 9000,
            "timeout_scan": 1800,
            "timeout_send": 600
        }
        self.create_test_config(config_data)

        settings = Settings(self.test_config_file)

        self.assertEqual(settings.server_address, "192.168.1.100")
        self.assertEqual(settings.server_port, 9000)
        self.assertEqual(settings.timeout_scan, 1800)
        self.assertEqual(settings.timeout_send, 600)

    def test_load_partial_config(self):
        """Test loading config with missing settings"""
        config_data = {
            "server_address": "10.0.0.1",
            "timeout_scan": 7200
        }
        self.create_test_config(config_data)

        settings = Settings(self.test_config_file)

        self.assertEqual(settings.server_address, "10.0.0.1")
        self.assertEqual(settings.timeout_scan, 7200)
        # Default values for missing settings
        self.assertEqual(settings.server_port, 8080)
        self.assertEqual(settings.timeout_send, 300)

    def test_load_invalid_json(self):
        """Test loading invalid JSON file"""
        with open(self.test_config_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")

        # Should not raise exception, should use default values
        settings = Settings(self.test_config_file)

        self.assertEqual(settings.server_address, "127.0.0.1")
        self.assertEqual(settings.server_port, 8080)

    def test_load_nonexistent_file(self):
        """Test loading non-existent config file"""
        settings = Settings("nonexistent_file.json")

        # Should use default values and create the file
        self.assertEqual(settings.server_address, "127.0.0.1")
        self.assertTrue(os.path.exists("nonexistent_file.json"))

        # Clean up
        os.remove("nonexistent_file.json")

    def test_save_settings(self):
        """Test saving settings to file"""
        settings = Settings(self.test_config_file)

        # Modify settings
        settings.server_address = "192.168.1.200"
        settings.server_port = 8081
        settings.timeout_scan = 7200
        settings.timeout_send = 1200

        settings.save()

        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(self.test_config_file))

        with open(self.test_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["server_address"], "192.168.1.200")
        self.assertEqual(saved_data["server_port"], 8081)
        self.assertEqual(saved_data["timeout_scan"], 7200)
        self.assertEqual(saved_data["timeout_send"], 1200)

    def test_server_address_validation_valid(self):
        """Test valid server address values"""
        settings = Settings(self.test_config_file)

        valid_addresses = [
            "127.0.0.1",
            "192.168.1.1",
            "10.0.0.1",
            "255.255.255.255",
            "0.0.0.0",
            "8.8.8.8"
        ]

        for address in valid_addresses:
            with self.subTest(address=address):
                settings.server_address = address
                self.assertEqual(settings.server_address, address)

    def test_server_address_validation_invalid(self):
        """Test invalid server address values"""
        settings = Settings(self.test_config_file)

        invalid_addresses = [
            "invalid_ip",
            "192.168.1.256",
            "192.168.1.",
            "192.168.1",
            "192.168.1.1.1",
            "192.168.1.-1",
            "",
            None,
            12345
        ]

        for address in invalid_addresses:
            with self.subTest(address=address):
                with self.assertRaises(ValueError):
                    settings.server_address = address

    def test_server_port_validation_valid(self):
        """Test valid server port values"""
        settings = Settings(self.test_config_file)

        valid_ports = [0, 1, 80, 443, 8080, 65535]

        for port in valid_ports:
            with self.subTest(port=port):
                settings.server_port = port
                self.assertEqual(settings.server_port, port)

    def test_server_port_validation_invalid(self):
        """Test invalid server port values"""
        settings = Settings(self.test_config_file)

        invalid_ports = [
            -1,
            -100,
            65536,
            70000,
            "invalid",
            "8080",  # string that can be converted, but should fail type check
            None,
            80.5
        ]

        for port in invalid_ports:
            with self.subTest(port=port):
                with self.assertRaises(ValueError):
                    settings.server_port = port

    def test_timeout_validation_valid(self):
        """Test valid timeout values"""
        settings = Settings(self.test_config_file)

        valid_timeouts = [0, 1, 60, 3600, 86400, 1000000]

        for timeout in valid_timeouts:
            with self.subTest(timeout=timeout):
                settings.timeout_scan = timeout
                settings.timeout_send = timeout
                self.assertEqual(settings.timeout_scan, timeout)
                self.assertEqual(settings.timeout_send, timeout)

    def test_timeout_validation_invalid(self):
        """Test invalid timeout values"""
        settings = Settings(self.test_config_file)

        invalid_timeouts = [
            -1,
            -100,
            "invalid",
            "3600",  # string that can be converted
            None,
            60.5
        ]

        for timeout in invalid_timeouts:
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    settings.timeout_scan = timeout
                with self.assertRaises(ValueError):
                    settings.timeout_send = timeout

    def test_unknown_settings_in_config(self):
        """Test handling of unknown settings in config file"""
        config_data = {
            "server_address": "192.168.1.1",
            "unknown_setting": "some_value",
            "another_unknown": 123
        }
        self.create_test_config(config_data)

        # Should not raise exception, should ignore unknown settings
        settings = Settings(self.test_config_file)

        self.assertEqual(settings.server_address, "192.168.1.1")
        # Default values for other settings
        self.assertEqual(settings.server_port, 8080)

    def test_to_dict_method(self):
        """Test to_dict method"""
        settings = Settings(self.test_config_file)

        settings_dict = settings.to_dict()

        expected_dict = {
            'server_address': '127.0.0.1',
            'server_port': 8080,
            'timeout_scan': 3600,
            'timeout_send': 300
        }

        self.assertEqual(settings_dict, expected_dict)
        # Verify it's a copy, not a reference
        settings_dict['server_port'] = 9999
        self.assertEqual(settings.server_port, 8080)

    def test_update_method_valid(self):
        """Test update method with valid values"""
        settings = Settings(self.test_config_file)

        settings.update(
            server_address="10.0.0.1",
            server_port=9090,
            timeout_scan=1800,
            timeout_send=600
        )

        self.assertEqual(settings.server_address, "10.0.0.1")
        self.assertEqual(settings.server_port, 9090)
        self.assertEqual(settings.timeout_scan, 1800)
        self.assertEqual(settings.timeout_send, 600)

    def test_update_method_invalid(self):
        """Test update method with invalid values"""
        settings = Settings(self.test_config_file)

        with self.assertRaises(ValueError):
            settings.update(
                server_address="invalid_ip",
                server_port=70000
            )

        # Verify settings were not changed
        self.assertEqual(settings.server_address, "127.0.0.1")
        self.assertEqual(settings.server_port, 8080)

    def test_update_method_unknown_setting(self):
        """Test update method with unknown setting"""
        settings = Settings(self.test_config_file)

        with self.assertRaises(ValueError):
            settings.update(
                server_address="192.168.1.1",
                unknown_setting="value"
            )

    def test_reset_to_defaults(self):
        """Test reset_to_defaults method"""
        settings = Settings(self.test_config_file)

        # Modify settings
        settings.server_address = "192.168.1.1"
        settings.server_port = 9000
        settings.timeout_scan = 1800
        settings.timeout_send = 600

        # Reset to defaults
        settings.reset_to_defaults()

        self.assertEqual(settings.server_address, "127.0.0.1")
        self.assertEqual(settings.server_port, 8080)
        self.assertEqual(settings.timeout_scan, 3600)
        self.assertEqual(settings.timeout_send, 300)

    def test_string_representation(self):
        """Test __str__ method"""
        settings = Settings(self.test_config_file)

        str_repr = str(settings)

        self.assertIn("server_address: 127.0.0.1", str_repr)
        self.assertIn("server_port: 8080", str_repr)
        self.assertIn("timeout_scan: 3600", str_repr)
        self.assertIn("timeout_send: 300", str_repr)

    def test_repr_representation(self):
        """Test __repr__ method"""
        settings = Settings(self.test_config_file)

        repr_repr = repr(settings)

        self.assertIn("Settings", repr_repr)
        self.assertIn(self.test_config_file, repr_repr)
        self.assertIn("server_address", repr_repr)

    def test_numeric_string_conversion(self):
        """Test that numeric strings are properly converted"""
        config_data = {
            "server_port": "8080",  # string instead of int
            "timeout_scan": "3600",  # string instead of int
            "timeout_send": "300"  # string instead of int
        }
        self.create_test_config(config_data)

        # Should handle string to int conversion
        settings = Settings(self.test_config_file)

        self.assertEqual(settings.server_port, 8080)
        self.assertEqual(settings.timeout_scan, 3600)
        self.assertEqual(settings.timeout_send, 300)

    def test_empty_config_file(self):
        """Test loading empty config file"""
        with open(self.test_config_file, 'w', encoding='utf-8') as f:
            f.write("{}")

        settings = Settings(self.test_config_file)

        # Should use all default values
        self.assertEqual(settings.server_address, "127.0.0.1")
        self.assertEqual(settings.server_port, 8080)
        self.assertEqual(settings.timeout_scan, 3600)
        self.assertEqual(settings.timeout_send, 300)


class TestSettingsIntegration(unittest.TestCase):
    """Integration tests for Settings class"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.temp_dir, "integration_test_config.json")

    def tearDown(self):
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_save_and_reload(self):
        """Test saving settings and reloading them"""
        # Create initial settings and modify
        settings1 = Settings(self.test_config_file)
        settings1.server_address = "192.168.1.100"
        settings1.server_port = 9090
        settings1.timeout_scan = 7200
        settings1.timeout_send = 1200
        settings1.save()

        # Create new settings instance and load
        settings2 = Settings(self.test_config_file)

        # Verify loaded values match saved values
        self.assertEqual(settings2.server_address, "192.168.1.100")
        self.assertEqual(settings2.server_port, 9090)
        self.assertEqual(settings2.timeout_scan, 7200)
        self.assertEqual(settings2.timeout_send, 1200)

    def test_multiple_instances_same_file(self):
        """Test multiple instances accessing the same config file"""
        settings1 = Settings(self.test_config_file)
        settings1.server_port = 8081
        settings1.save()

        settings2 = Settings(self.test_config_file)
        self.assertEqual(settings2.server_port, 8081)

        settings2.server_port = 8082
        settings2.save()

        settings3 = Settings(self.test_config_file)
        self.assertEqual(settings3.server_port, 8082)
