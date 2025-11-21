import threading
import time
import json
from datetime import datetime
from agent.windows import WindowsScanner  # Импортируем наш предыдущий класс


class WindowsService:
    """
    Background service for managing Windows software scanning
    """

    def __init__(self, scan_interval=3600):  # default 1 hour
        """
        Initialize Windows service

        Args:
            scan_interval (int): interval between automatic scans in seconds
        """
        self.scanner = WindowsScanner()
        self.scan_interval = scan_interval
        self.is_running = False
        self.service_thread = None
        self.last_scan_time = None
        self.scan_count = 0

        # Event callbacks (можно добавить позже для уведомлений)
        self.on_scan_start = None
        self.on_scan_complete = None
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

                # Заглушка для демонстрации - сканируем каждые scan_interval секунд
                if (self.last_scan_time is None or
                        (datetime.now() - self.last_scan_time).total_seconds() >= self.scan_interval):
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
            'scan_interval': self.scan_interval,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'scan_count': self.scan_count,
            'thread_alive': self.service_thread.is_alive() if self.service_thread else False
        }

    def set_scan_interval(self, interval_seconds):
        """
        Set new scan interval

        Args:
            interval_seconds (int): new interval in seconds
        """
        self.scan_interval = interval_seconds
        print(f"[Service] Scan interval set to {interval_seconds} seconds")

    def register_callbacks(self, on_scan_start=None, on_scan_complete=None, on_data_request=None):
        """
        Register callback functions for service events

        Args:
            on_scan_start: called when scan starts
            on_scan_complete: called when scan completes (with data)
            on_data_request: called when data is requested
        """
        self.on_scan_start = on_scan_start
        self.on_scan_complete = on_scan_complete
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
