import subprocess
from fastapi import APIRouter, Form, HTTPException
import logging

router = APIRouter(
    prefix="/wifi",
    tags=["wifi"],
    responses={404: {"detail": "Not found"}},
)

logger = logging.getLogger(__name__)


def connect_to_wifi(ssid: str, psk: str):
    try:
        # Ensure the wlan0 interface is up
        subprocess.run(["ifconfig", "wlan0", "up"], check=True)

        # Add a new network
        network_id = subprocess.check_output(["wpa_cli", "-i", "wlan0", "add_network"]).strip()

        # Set the SSID
        subprocess.run(["wpa_cli", "-i", "wlan0", "set_network", network_id, "ssid", f'"{ssid}"'], check=True)

        # Set the PSK
        subprocess.run(["wpa_cli", "-i", "wlan0", "set_network", network_id, "psk", f'"{psk}"'], check=True)

        # Enable the network
        subprocess.run(["wpa_cli", "-i", "wlan0", "enable_network", network_id], check=True)

        # Select the network
        subprocess.run(["wpa_cli", "-i", "wlan0", "select_network", network_id], check=True)

        # Save the configuration
        subprocess.run(["wpa_cli", "-i", "wlan0", "save_config"], check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error configuring Wi-Fi: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure Wi-Fi: {e}")


@router.post("/configure_wifi")
async def configure_wifi(ssid: str = Form(...), password: str = Form(...)):
    try:
        connect_to_wifi(ssid, password)
        return {
            "status": "success",
            "message": "Wi-Fi configuration updated. Please manually restart the Raspberry Pi to apply the changes."
        }
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}

