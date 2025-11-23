# handlers.py
from aiohttp import web
import json
from datetime import datetime
import logging

# Get logger
logger = logging.getLogger("AgentHandler")


async def agent_data_handler(request):
    """
    Handle POST /api/v1/agent/data
    Receive complete agent data
    """
    try:
        # Get the main app instance
        # Parse JSON data
        try:
            data = await request.json()
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            return web.json_response(
                {"error": "Invalid JSON data"},
                status=400
            )
        # Log the received data
        hostname = data.get('system_info', {}).get('system', {}).get('hostname', 'Unknown')
        logger.info(f"Received agent data from: {hostname}")

        return web.json_response({
            "status": "success",
            "message": "Agent data received successfully",
            "received_timestamp": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error processing agent data: {str(e)}")
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


def print_agent_data(data: dict):
    """Print received agent data to console"""
    print("\n" + "=" * 80)
    print("📨 RECEIVED AGENT DATA")
    print("=" * 80)

    # Basic info
    print(f"Timestamp: {data.get('scan_timestamp', 'Unknown')}")

    # System info
    system_info = data.get('system_info', {})
    if system_info:
        system_data = system_info.get('system', {})
        print(f"Hostname: {system_data.get('hostname', 'Unknown')}")
        print(f"Platform: {system_data.get('platform', 'Unknown')} "
              f"{system_data.get('platform_release', '')}")
        print(f"Architecture: {system_data.get('architecture', 'Unknown')}")

        # Hardware summary
        hardware_info = system_info.get('hardware', {})
        if hardware_info:
            cpu_info = hardware_info.get('cpu', {})
            cpu_name = cpu_info.get('name') or cpu_info.get('processor', 'Unknown')
            print(f"CPU: {cpu_name}")

            memory_info = hardware_info.get('memory', {})
            memory_gb = memory_info.get('total_physical_memory_gb', 'Unknown')
            print(f"Memory: {memory_gb} GB")

        # Network info
        network_info = system_info.get('network', {})
        if network_info:
            print(f"IP Address: {network_info.get('ip_address', 'Unknown')}")
            print(f"MAC Address: {network_info.get('mac_address', 'Unknown')}")

        # BIOS info
        bios_info = system_info.get('bios', {})
        if bios_info:
            print(f"BIOS Serial: {bios_info.get('serial_number', 'Unknown')}")

    # Software info
    software_count = data.get('software_count', 0)
    software_list = data.get('software_list', [])
    print(f"Software Count: {software_count}")

    # Print first 5 software items
    if software_list:
        print(f"\n--- FIRST 5 SOFTWARE ITEMS (out of {len(software_list)}) ---")
        for i, software in enumerate(software_list[:5]):
            print(f"  {i + 1}. {software.get('name', 'Unknown')} "
                  f"[v{software.get('version', 'Unknown')}]")

    print("=" * 80 + "\n")