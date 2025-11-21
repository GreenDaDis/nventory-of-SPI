from windows.scanner import WindowsScanner


# Example usage
if __name__ == "__main__":
    # Create scanner instance
    scanner = WindowsScanner()

    # Get data (if cache is empty - scan will start)
    print("=== GETTING DATA ===")
    data = scanner.get_data()

    print(f"\n=== RESULTS ===")
    print(f"Scan timestamp: {data['scan_timestamp']}")
    print(f"Total software: {data['software_count']}")
    print(f"From registry: {data['sources']['registry']}")
    print(f"From WMIC: {data['sources']['wmic']}")

    # Show first 10 programs
    print(f"\n=== FIRST 10 SOFTWARE ===")
    for i, software in enumerate(data['software_list'][:10]):
        print(f"{i + 1:2d}. {software['name']}")
        print(f"     Version: {software['version'] or 'N/A'}")
        print(f"     Vendor: {software['vendor'] or 'N/A'}")
        print(f"     Install date: {software['install_date'] or 'N/A'}")
        print(f"     Update date: {software['update_date'] or 'N/A'}")
        print()

    # Demonstrate cache usage
    print("\n=== CACHE CHECK ===")
    print("Requesting data again (should be from cache):")
    cached_data = scanner.get_data()
    print(f"Data from cache: {cached_data['software_count']} software")

    # Additional methods demonstration
    print("\n=== ADDITIONAL METHODS ===")
    software_names = scanner.get_software_names()[:5]
    print(f"First 5 software names: {software_names}")

    # Find software by pattern
    print("\n=== FINDING SOFTWARE ===")
    browser_software = scanner.find_software_by_name("chrome")[:3]
    print(f"Found {len(browser_software)} software with 'chrome':")
    for software in browser_software:
        print(f"  - {software['name']} (v{software['version']})")

    # Clear cache
    print("\n=== CLEARING CACHE ===")
    scanner.clear_cache()
    print("Cache cleared, next get_data() will trigger scan")