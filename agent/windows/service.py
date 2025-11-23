import threading
import time
import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

from ..settings import Settings
from scanner import WindowsScanner

class WindowsService:
    """
    Background service for managing Windows software scanning
    """

    def __init__(self, settings: Settings):  # default 1 hour
        """
        Initialize Windows service

        Args:
            settings: Settings for Service.
        """
        self.scanner = WindowsScanner()
        self.settings = settings
        self.is_running = False
        self.service_thread = None
        self.last_scan_time = None
        self.scan_count = 0
        self.last_send_time = None
        self.send_count = 0

        # Event callbacks (можно добавить позже для уведомлений)
        self.on_scan_start = None
        self.on_scan_complete = None
        self.on_send_start = None
        self.on_send_complete = None
        self.on_data_request = None

    def start(self):
        """
        Start the background service
        """
        if self.is_running:
            print("Service is already running")
            return False

        print("Starting Windows Service...")
        self.is_running = True

        # Запускаем фоновый поток
        self.service_thread = threading.Thread(target=self._service_loop, daemon=True)
        self.service_thread.start()

        # Выполняем первоначальное сканирование
        self._trigger_scan()

        print("Windows Service started successfully")
        return True

    def stop(self):
        """
        Stop the background service
        """
        if not self.is_running:
            print("Service is not running")
            return False

        print("Stopping Windows Service...")
        self.is_running = False

        if self.service_thread and self.service_thread.is_alive():
            self.service_thread.join(timeout=5)

        print("Windows Service stopped")
        return True

    def _send_data_to_server(self, data: Dict[str, Any]) -> bool:
        """
        Send scanned data to the server

        Args:
            data: Data to send. If None, will perform new scan

        Returns:
            bool: True if successful, False otherwise
        """
        # Формируем полный URL сервера
        server_url = f"http://{self.settings.server_address}:{self.settings.server_port}/api/v1/agent/data"

        print(f"[Service] Sending data to server: {server_url}")
        print(f"[Service] Data size: {len(str(data))} bytes, software items: {data.get('software_count', 0)}")

        # Отправляем POST запрос
        response = requests.post(
            server_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30  # 30 секунд таймаут
        )

        # Проверяем ответ
        if response.status_code == 200:
            result = response.json()
            print(f"[Service] Data successfully sent to server. Response: {result.get('message', 'Unknown')}")
            return True
        else:
            print(f"[Service] Server returned error: {response.status_code} - {response.text}")
            return False

    def _service_loop(self):
        """
        Main service loop running in background thread
        """
        print("Service loop started")

        while self.is_running:
            try:
                # Здесь будет логика по расписанию
                # Пока просто ждем и проверяем флаг
                time.sleep(1)

                # Заглушка для демонстрации - сканируем каждые timeout_scan секунд
                if (self.last_scan_time is None or
                        (datetime.now() - self.last_scan_time).total_seconds() >= self.settings.timeout_scan):
                    self._trigger_scan()

                # Заглушка для демонстрации - сканируем каждые scan_interval секунд
                if (self.last_send_time is None or
                        (datetime.now() - self.last_send_time).total_seconds() >= self.settings.timeout_send):
                    self._trigger_scan()

            except Exception as e:
                print(f"Error in service loop: {e}")
                time.sleep(10)  # Wait before retrying

    def _trigger_scan(self):
        """
        Trigger a new scan
        """
        try:
            if self.on_scan_start:
                self.on_scan_start()

            print(f"[Service] Starting scan #{self.scan_count + 1}...")
            data = self.scanner.scan()
            self.last_scan_time = datetime.now()
            self.scan_count += 1

            print(f"[Service] Scan #{self.scan_count} completed. Found {data['software_count']} software")

            if self.on_scan_complete:
                self.on_scan_complete(data)

        except Exception as e:
            print(f"[Service] Scan error: {e}")

    def _trigger_send(self):
        """
        Trigger a new send
        """
        try:
            if self.on_send_start:
                self.on_send_start()

            print(f"[Service] Starting send #{self.send_count + 1}...")
            data = self.scanner.scan()
            self.last_send_time = datetime.now()
            self.send_count += 1
            self._send_data_to_server(data)
            print(f"[Service] Send #{self.send_count} completed.")

            if self.on_send_complete:
                self.on_send_complete()

        except Exception as e:
            print(f"[Service] Scan error: {e}")

    def get_software_data(self):
        """
        Get current software data (uses cache if available)

        Returns:
            dict: software data
        """
        try:
            if self.on_data_request:
                self.on_data_request()

            print("[Service] Getting software data...")
            data = self.scanner.get_data()
            return data

        except Exception as e:
            print(f"[Service] Error getting data: {e}")
            return None

    def force_scan(self):
        """
        Force immediate scan regardless of schedule
        """
        print("[Service] Forcing immediate scan...")
        self._trigger_scan()

    def get_service_status(self):
        """
        Get service status information

        Returns:
            dict: service status
        """
        return {
            'is_running': self.is_running,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'scan_count': self.scan_count,
            'thread_alive': self.service_thread.is_alive() if self.service_thread else False
        }

    def register_callbacks(self, on_scan_start=None, on_scan_complete=None, on_send_start=None, on_send_complete=None, on_data_request=None):
        """
        Register callback functions for service events

        Args:
            on_scan_start: called when scan starts
            on_scan_complete: called when scan completes (with data)
            on_send_start: called when send starts
            on_send_complete: called when send completes
            on_data_request: called when data is requested
        """
        self.on_scan_start = on_scan_start
        self.on_scan_complete = on_scan_complete
        self.on_send_start = on_send_start
        self.on_send_complete = on_send_complete
        self.on_data_request = on_data_request

    def find_software(self, name_pattern):
        """
        Find software by name pattern

        Args:
            name_pattern (str): pattern to search for

        Returns:
            list: matching software
        """
        return self.scanner.find_software_by_name(name_pattern)

    def get_software_names(self):
        """
        Get list of all software names

        Returns:
            list: software names
        """
        return self.scanner.get_software_names()
