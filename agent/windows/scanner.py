import winreg
import subprocess
import csv
from datetime import datetime

from system import SystemInfo


class WindowsScanner:
    """
    Class for scanning installed software in Windows
    """

    def __init__(self):
        """
        Initialize scanner
        """
        self.cache_data = None
        self.system_info = SystemInfo()

    def _get_software_from_registry(self):
        """
        Collect installed software information from Windows registry

        Returns:
            list: list of dictionaries with software information
        """
        software_list = []
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for hive, path in registry_paths:
            try:
                key = winreg.OpenKey(hive, path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)

                        software = {}
                        try:
                            software['name'] = winreg.QueryValueEx(subkey, 'DisplayName')[0]
                        except FileNotFoundError:
                            winreg.CloseKey(subkey)
                            continue

                        # Basic information
                        try:
                            software['version'] = winreg.QueryValueEx(subkey, 'DisplayVersion')[0]
                        except FileNotFoundError:
                            software['version'] = None

                        try:
                            software['vendor'] = winreg.QueryValueEx(subkey, 'Publisher')[0]
                        except FileNotFoundError:
                            software['vendor'] = None

                        # Installation and update dates
                        try:
                            install_date = winreg.QueryValueEx(subkey, 'InstallDate')[0]
                            software['install_date'] = self._parse_install_date(install_date)
                        except FileNotFoundError:
                            software['install_date'] = None

                        # For update date use registry key modification time
                        try:
                            mod_time = winreg.QueryInfoKey(subkey)[2]
                            software['update_date'] = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            software['update_date'] = None

                        software['source'] = 'registry'
                        software_list.append(software)

                        winreg.CloseKey(subkey)
                    except (FileNotFoundError, PermissionError, OSError):
                        continue

                winreg.CloseKey(key)
            except (FileNotFoundError, PermissionError):
                continue

        return software_list

    def _get_software_from_wmic(self):
        """
        Collect installed software information via WMIC

        Returns:
            list: list of dictionaries with software information
        """
        software_list = []
        try:
            # Используем другую кодировку для WMIC
            result = subprocess.run(
                ['wmic', 'product', 'get', 'Name,Version,Vendor,InstallDate', '/format:csv'],
                capture_output=True,
                text=True,
                encoding='cp866',  # Изменяем кодировку для русской Windows
                timeout=30
            )

            if result.returncode != 0:
                print(f"WMIC returned error code: {result.returncode}")
                return software_list

            lines = result.stdout.strip().split('\n')

            if len(lines) > 1:
                reader = csv.DictReader(lines)
                for row in reader:
                    if row.get('Name') and row['Name'].strip():
                        software = {
                            'name': row.get('Name', '').strip(),
                            'version': row.get('Version', '').strip(),
                            'vendor': row.get('Vendor', '').strip(),
                            'install_date': self._parse_wmic_date(row.get('InstallDate', '')),
                            'update_date': None,
                            'source': 'wmic'
                        }
                        software_list.append(software)

        except subprocess.TimeoutExpired:
            print("WMIC timeout - skipping WMIC data")
        except subprocess.CalledProcessError as e:
            print(f"WMIC process error: {e}")
        except Exception as e:
            print(f"WMIC general error: {e}")

        return software_list

    def _parse_install_date(self, date_str):
        """
        Parse installation date from various formats

        Args:
            date_str (str): date string

        Returns:
            str: formatted date or original string
        """
        if not date_str:
            return None

        # Format YYYYMMDD
        if len(date_str) == 8 and date_str.isdigit():
            try:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except:
                pass

        return date_str

    def _parse_wmic_date(self, wmic_date):
        """
        Parse date from WMIC format (YYYYMMDDHHMMSS.XXXXXX+XXX)

        Args:
            wmic_date (str): date in WMIC format

        Returns:
            str: formatted date
        """
        if not wmic_date or len(wmic_date) < 8:
            return None

        try:
            # Take only YYYYMMDD part
            date_part = wmic_date[:8]
            return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
        except:
            return wmic_date

    def _merge_software_lists(self, registry_list, wmic_list):
        """
        Merge lists from different sources, remove duplicates

        Args:
            registry_list (list): list from registry
            wmic_list (list): list from WMIC

        Returns:
            list: merged list without duplicates
        """
        merged_list = []
        seen_names = set()

        # First add from registry (more programs)
        for software in registry_list:
            name_lower = software['name'].lower()
            if name_lower not in seen_names:
                merged_list.append(software)
                seen_names.add(name_lower)

        # Then add from WMIC what's not in registry
        for software in wmic_list:
            name_lower = software['name'].lower()
            if name_lower not in seen_names:
                merged_list.append(software)
                seen_names.add(name_lower)

        return merged_list

    def scan(self):
        """
        Public method for scanning installed software

        Returns:
            dict: JSON object with scan results
        """
        # Collect data from different sources
        registry_software = self._get_software_from_registry()
        wmic_software = self._get_software_from_wmic()

        # Merge results
        all_software = self._merge_software_lists(registry_software, wmic_software)

        # Sort by name
        all_software.sort(key=lambda x: x['name'].lower())

        # Create result with proper structure
        result = {
            'system_info': self.system_info.collect_all_info(),
            'scan_timestamp': datetime.now().isoformat(),
            'software_count': len(all_software),
            'software_list': all_software
        }

        # Save to memory cache
        self.cache_data = result
        return result

    def get_data(self):
        """
        Public method for getting installed software data

        Returns:
            dict: JSON object with installed software data
        """
        # Check memory cache first
        if self.cache_data is not None:
            print("Data loaded from memory cache")
            return self.cache_data
        else:
            print("Cache is empty, starting scan...")
            return self.scan()

    def clear_cache(self):
        """
        Clear memory cache
        """
        self.cache_data = None

    def get_software_names(self):
        """
        Get only software names from cache

        Returns:
            list: list of software names
        """
        if self.cache_data is None:
            self.get_data()

        return [software['name'] for software in self.cache_data['software_list']]

    def find_software_by_name(self, name_pattern):
        """
        Find software by name pattern (case-insensitive)

        Args:
            name_pattern (str): pattern to search for

        Returns:
            list: list of matching software
        """
        if self.cache_data is None:
            self.get_data()

        pattern_lower = name_pattern.lower()
        return [
            software for software in self.cache_data['software_list']
            if pattern_lower in software['name'].lower()
        ]
