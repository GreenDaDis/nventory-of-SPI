# system_info.py
import platform
import socket
import uuid
import json
import subprocess
import re
from typing import Dict, Any, Optional


class SystemInfo:
    """
    Class for collecting system information
    """

    def __init__(self):
        self._cached_info: Optional[Dict[str, Any]] = {
            "system": self._get_system_info(),
            "hardware": self._get_hardware_info(),
            "network": self._get_network_info(),
            "bios": self._get_bios_info(),
            "collection_timestamp": self._get_timestamp()
        }

    def collect_all_info(self) -> Dict[str, Any]:
        """
        Collect all system information

        Returns:
            dict: Complete system information
        """
        if self._cached_info is not None:
            return self._cached_info

        self._cached_info = {
            "system": self._get_system_info(),
            "hardware": self._get_hardware_info(),
            "network": self._get_network_info(),
            "bios": self._get_bios_info(),
            "collection_timestamp": self._get_timestamp()
        }
        return self._cached_info

    def _get_system_info(self) -> Dict[str, str]:
        """Get operating system information"""
        try:
            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.architecture()[0],
                "hostname": socket.gethostname(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            }
        except Exception as e:
            return {"error": f"Failed to get system info: {str(e)}"}

    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information"""
        try:
            hardware_info = {}

            # CPU information
            hardware_info["cpu"] = self._get_cpu_info()

            # Memory information
            hardware_info["memory"] = self._get_memory_info()

            # Disk information
            hardware_info["disks"] = self._get_disk_info()

            return hardware_info

        except Exception as e:
            return {"error": f"Failed to get hardware info: {str(e)}"}

    def _get_cpu_info(self) -> Dict[str, str]:
        """Get CPU information"""
        try:
            cpu_info = {
                "processor": platform.processor(),
                "cores": str(self._get_cpu_cores()),
                "architecture": platform.machine()
            }

            # Try to get more detailed CPU info on Windows
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ['wmic', 'cpu', 'get', 'Name,NumberOfCores,NumberOfLogicalProcessors', '/format:list'],
                        capture_output=True, text=True, encoding='utf-8'
                    )
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'Name=' in line:
                                cpu_info["name"] = line.split('=', 1)[1].strip()
                            elif 'NumberOfCores=' in line:
                                cpu_info["physical_cores"] = line.split('=', 1)[1].strip()
                            elif 'NumberOfLogicalProcessors=' in line:
                                cpu_info["logical_cores"] = line.split('=', 1)[1].strip()
                except:
                    pass

            return cpu_info

        except Exception as e:
            return {"error": f"Failed to get CPU info: {str(e)}"}

    def _get_cpu_cores(self) -> int:
        """Get number of CPU cores"""
        try:
            return int(subprocess.run(
                ['wmic', 'cpu', 'get', 'NumberOfCores', '/format:value'],
                capture_output=True, text=True
            ).stdout.strip().split('=')[1])
        except:
            try:
                import os
                return os.cpu_count() or 1
            except:
                return 1

    def _get_memory_info(self) -> Dict[str, str]:
        """Get memory information"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/format:value'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    total_memory = result.stdout.strip().split('=')[1]
                    return {
                        "total_physical_memory_bytes": total_memory,
                        "total_physical_memory_gb": str(round(int(total_memory) / (1024 ** 3), 2))
                    }
            return {"total_physical_memory": "Unknown"}
        except Exception as e:
            return {"error": f"Failed to get memory info: {str(e)}"}

    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk information"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'logicaldisk', 'where', 'drivetype=3', 'get', 'DeviceID,Size,FreeSpace', '/format:list'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    disks = {}
                    current_disk = {}

                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line.startswith('DeviceID='):
                            if current_disk:
                                disk_id = current_disk.get('DeviceID', 'Unknown')
                                disks[disk_id] = current_disk.copy()
                            current_disk = {'DeviceID': line.split('=', 1)[1]}
                        elif line.startswith('Size='):
                            size_bytes = line.split('=', 1)[1]
                            current_disk['SizeBytes'] = size_bytes
                            current_disk['SizeGB'] = str(round(int(size_bytes) / (1024 ** 3), 2))
                        elif line.startswith('FreeSpace='):
                            free_bytes = line.split('=', 1)[1]
                            current_disk['FreeSpaceBytes'] = free_bytes
                            current_disk['FreeSpaceGB'] = str(round(int(free_bytes) / (1024 ** 3), 2))

                    # Add the last disk
                    if current_disk:
                        disk_id = current_disk.get('DeviceID', 'Unknown')
                        disks[disk_id] = current_disk

                    return disks

            return {"info": "Disk information available only on Windows"}
        except Exception as e:
            return {"error": f"Failed to get disk info: {str(e)}"}

    def _get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            network_info = {
                "hostname": socket.gethostname(),
                "fqdn": socket.getfqdn(),
                "mac_address": self._get_mac_address(),
                "ip_address": self._get_ip_address()
            }

            # Try to get more network info on Windows
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ['ipconfig', '/all'],
                        capture_output=True, text=True, encoding='utf-8'
                    )
                    if result.returncode == 0:
                        network_info["detailed"] = self._parse_ipconfig(result.stdout)
                except:
                    pass

            return network_info

        except Exception as e:
            return {"error": f"Failed to get network info: {str(e)}"}

    def _get_mac_address(self) -> str:
        """Get MAC address"""
        try:
            mac = uuid.getnode()
            return ':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        except:
            return "Unknown"

    def _get_ip_address(self) -> str:
        """Get IP address"""
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            return ip_address
        except:
            return "Unknown"

    def _parse_ipconfig(self, ipconfig_output: str) -> Dict[str, Any]:
        """Parse ipconfig /all output"""
        try:
            interfaces = {}
            current_interface = None

            for line in ipconfig_output.split('\n'):
                line = line.strip()

                # New interface section
                if line and not line.startswith(' ') and line.endswith(':'):
                    if current_interface:
                        interfaces[current_interface['name']] = current_interface
                    current_interface = {'name': line.rstrip(':'), 'properties': {}}

                # Interface properties
                elif current_interface and ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if key and value:
                        current_interface['properties'][key] = value

            # Add the last interface
            if current_interface:
                interfaces[current_interface['name']] = current_interface

            return interfaces

        except Exception as e:
            return {"error": f"Failed to parse ipconfig: {str(e)}"}

    def _get_bios_info(self) -> Dict[str, str]:
        """Get BIOS information"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'bios', 'get', 'SerialNumber,Version,Manufacturer', '/format:list'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    bios_info = {}
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if 'SerialNumber=' in line:
                            bios_info["serial_number"] = line.split('=', 1)[1]
                        elif 'Version=' in line:
                            bios_info["version"] = line.split('=', 1)[1]
                        elif 'Manufacturer=' in line:
                            bios_info["manufacturer"] = line.split('=', 1)[1]

                    return bios_info

            return {"info": "BIOS information available only on Windows"}
        except Exception as e:
            return {"error": f"Failed to get BIOS info: {str(e)}"}

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_unique_identifier(self) -> str:
        """
        Get unique system identifier

        Returns:
            str: Unique identifier based on system properties
        """
        try:
            # Combine multiple system properties for uniqueness
            system_info = self.collect_all_info()

            identifiers = []

            # Use BIOS serial number if available
            bios_serial = system_info.get("bios", {}).get("serial_number")
            if bios_serial and bios_serial not in ["", "Unknown", "To be filled by O.E.M."]:
                identifiers.append(bios_serial)

            # Use MAC address
            mac = system_info.get("network", {}).get("mac_address", "Unknown")
            if mac != "Unknown":
                identifiers.append(mac)

            # Use hostname
            hostname = system_info.get("system", {}).get("hostname", "Unknown")
            identifiers.append(hostname)

            # Create a unique hash
            import hashlib
            identifier_string = "-".join(identifiers)
            return hashlib.sha256(identifier_string.encode()).hexdigest()[:32]

        except Exception as e:
            return f"unknown_system_{hash(str(e))}"

    def to_json(self) -> str:
        """
        Convert system info to JSON string

        Returns:
            str: JSON formatted system information
        """
        return json.dumps(self.collect_all_info(), indent=2, ensure_ascii=False)

    def clear_cache(self) -> None:
        """Clear cached system information"""
        self._cached_info = None

    def refresh(self) -> Dict[str, Any]:
        """
        Refresh and recollect system information

        Returns:
            dict: Updated system information
        """
        self.clear_cache()
        return self.collect_all_info()
