import time

from settings import Settings
from agent.windows import WindowsService


# Пример использования с демонстрацией
if __name__ == "__main__":
    setting = Settings()
    # Создаем callback функции для демонстрации
    def on_scan_start():
        print("🎯 [Callback] Scan started!")


    def on_scan_complete(data):
        print(f"✅ [Callback] Scan completed! Found {data['software_count']} items")

    def on_send_start():
        print("🎯 [Callback] Send started!")

    def on_send_complete():
        print(f"✅ [Callback] Send completed!")


    def on_data_request():
        print("📊 [Callback] Data requested")


    # Создаем и настраиваем сервис
    service = WindowsService(setting)

    # Регистрируем callback'и
    service.register_callbacks(
        on_scan_start=on_scan_start,
        on_scan_complete=on_scan_complete,
        on_send_start=on_send_start,
        on_send_complete=on_send_complete,
        on_data_request=on_data_request
    )

    # Запускаем сервис
    print("=== STARTING SERVICE ===")
    service.start()

    try:
        # Демонстрация работы сервиса
        print("\n=== DEMONSTRATION ===")

        # Ждем немного для первого сканирования
        time.sleep(2)

        # Получаем данные
        print("\n1. Getting current data...")
        data = service.get_software_data()
        if data:
            print(f"   Current software count: {data['software_count']}")

        # Принудительное сканирование
        print("\n2. Forcing immediate scan...")
        service.force_scan()

        # Поиск ПО
        print("\n3. Searching for software...")
        browsers = service.find_software("chrome")
        print(f"   Found {len(browsers)} Chrome-related software")

        # Статус сервиса
        print("\n4. Service status:")
        status = service.get_service_status()
        for key, value in status.items():
            print(f"   {key}: {value}")

        # Ждем для демонстрации автоматического сканирования
        print("\n5. Waiting for automatic scan...")
        time.sleep(15)

        # Еще один статус
        print("\n6. Final service status:")
        status = service.get_service_status()
        for key, value in status.items():
            print(f"   {key}: {value}")

        # Даем сервису поработать еще немного
        print("\n=== SERVICE IS RUNNING IN BACKGROUND ===")
        print("Press Ctrl+C to stop...")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n=== STOPPING SERVICE ===")
        service.stop()

    print("Demo completed")