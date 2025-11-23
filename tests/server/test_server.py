import json
import unittest
from unittest.mock import patch, MagicMock
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from datetime import datetime

from server.handlers import agent_data_handler


class TestAgentDataHandler(AioHTTPTestCase):
    """Тесты для хендлера agent_data_handler"""

    async def get_application(self):
        """Создаем aiohttp приложение для тестов"""
        app = web.Application()
        app.router.add_post('/api/v1/agent/data', agent_data_handler)
        return app

    @unittest_run_loop
    async def test_successful_agent_data_processing(self):
        """Тест успешной обработки корректных данных агента"""
        # Подготовка тестовых данных
        test_data = {
            "scan_timestamp": datetime.now().isoformat(),
            "system_info": {
                "system": {
                    "platform": "Windows",
                    "platform_release": "10",
                    "platform_version": "10.0.19041",
                    "architecture": "64bit",
                    "hostname": "TEST-PC-01",
                    "processor": "Intel64 Family 6 Model 158 Stepping 10",
                    "python_version": "3.8.5"
                },
                "hardware": {
                    "cpu": {
                        "processor": "Intel64 Family 6 Model 158 Stepping 10",
                        "cores": "8",
                        "architecture": "AMD64"
                    },
                    "memory": {
                        "total_physical_memory_bytes": "17179869184",
                        "total_physical_memory_gb": "16.0"
                    }
                },
                "network": {
                    "hostname": "TEST-PC-01",
                    "fqdn": "TEST-PC-01.local",
                    "mac_address": "00:1B:44:11:3A:B7",
                    "ip_address": "192.168.1.100"
                },
                "bios": {
                    "serial_number": "S/N-1234567890",
                    "version": "F.60",
                    "manufacturer": "American Megatrends Inc."
                }
            },
            "software_count": 2,
            "software_list": [
                {
                    "name": "Google Chrome",
                    "version": "91.0.4472.124",
                    "vendor": "Google LLC",
                    "install_date": "2023-01-15",
                    "source": "registry"
                },
                {
                    "name": "Python 3.8.5",
                    "version": "3.8.5150.0",
                    "vendor": "Python Software Foundation",
                    "install_date": "2023-03-10",
                    "source": "registry"
                }
            ]
        }

        # Отправка POST запроса
        resp = await self.client.post('/api/v1/agent/data', json=test_data)

        # Проверки
        self.assertEqual(resp.status, 200)

        data = await resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['message'], 'Agent data received successfully')
        self.assertIn('received_timestamp', data)

    @unittest_run_loop
    async def test_invalid_json_data(self):
        """Тест обработки невалидного JSON"""
        # Отправка невалидного JSON
        resp = await self.client.post('/api/v1/agent/data',
                                      data='invalid json',
                                      headers={'Content-Type': 'application/json'})

        # Проверки
        self.assertEqual(resp.status, 400)

        data = await resp.json()
        self.assertEqual(data['error'], 'Invalid JSON data')

    @unittest_run_loop
    async def test_missing_hostname_in_data(self):
        """Тест обработки данных без hostname"""
        test_data = {
            "scan_timestamp": datetime.now().isoformat(),
            "system_info": {
                "system": {
                    # Отсутствует hostname
                    "platform": "Windows",
                    "platform_release": "10"
                }
            },
            "software_count": 0,
            "software_list": []
        }

        resp = await self.client.post('/api/v1/agent/data', json=test_data)

        # Должен вернуться успешный ответ, даже если hostname отсутствует
        self.assertEqual(resp.status, 200)

        data = await resp.json()
        self.assertEqual(data['status'], 'success')

    @unittest_run_loop
    async def test_empty_software_list(self):
        """Тест обработки данных с пустым списком ПО"""
        test_data = {
            "scan_timestamp": datetime.now().isoformat(),
            "system_info": {
                "system": {
                    "platform": "Windows",
                    "hostname": "TEST-PC-01"
                }
            },
            "software_count": 0,
            "software_list": []
        }

        resp = await self.client.post('/api/v1/agent/data', json=test_data)

        self.assertEqual(resp.status, 200)

        data = await resp.json()
        self.assertEqual(data['status'], 'success')

    @unittest_run_loop
    async def test_minimal_valid_data(self):
        """Тест обработки минимально валидных данных"""
        test_data = {
            "scan_timestamp": datetime.now().isoformat(),
            "system_info": {
                "system": {
                    "hostname": "MINIMAL-PC"
                }
            },
            "software_count": 0,
            "software_list": []
        }

        resp = await self.client.post('/api/v1/agent/data', json=test_data)

        self.assertEqual(resp.status, 200)

        data = await resp.json()
        self.assertEqual(data['status'], 'success')

    @unittest_run_loop
    async def test_wrong_http_method(self):
        """Тест вызова хендлера неправильным HTTP методом"""
        resp = await self.client.get('/api/v1/agent/data')
        self.assertEqual(resp.status, 405)  # Method Not Allowed


class TestAgentDataHandlerWithMocks(unittest.TestCase):
    """Тесты с моками для проверки ошибок"""

    def setUp(self):
        self.app = web.Application()
        self.app.router.add_post('/api/v1/agent/data', agent_data_handler)

    @patch('your_module.logger')
    async def test_exception_handling(self, mock_logger):
        """Тест обработки внутренних исключений"""
        # Создаем mock request, который вызовет исключение
        mock_request = MagicMock()
        mock_request.json.side_effect = Exception("Test exception")

        # Вызываем хендлер напрямую
        response = await agent_data_handler(mock_request)

        # Проверяем, что логгер был вызван
        mock_logger.error.assert_called()

        # Проверяем ответ
        self.assertEqual(response.status, 500)

        # Получаем тело ответа
        response_data = json.loads(response.text)
        self.assertEqual(response_data['error'], 'Internal server error')

    @patch('your_module.logger')
    async def test_json_decode_error(self, mock_logger):
        """Тест обработки ошибки декодирования JSON"""
        mock_request = MagicMock()
        mock_request.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)

        response = await agent_data_handler(mock_request)

        # Проверяем логирование
        mock_logger.error.assert_called_with("Invalid JSON received")

        # Проверяем ответ
        self.assertEqual(response.status, 400)

        response_data = json.loads(response.text)
        self.assertEqual(response_data['error'], 'Invalid JSON data')
