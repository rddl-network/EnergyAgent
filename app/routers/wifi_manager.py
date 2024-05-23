import subprocess
from fastapi import APIRouter, Form, HTTPException
import logging

router = APIRouter(
    prefix="/wifi",
    tags=["wifi"],
    responses={404: {"detail": "Not found"}},
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

WPA_SUPPLICANT_CONF = "/etc/wpa_supplicant/wpa_supplicant.conf"


def update_wpa_supplicant(ssid: str, psk: str):
    try:
        # Backup the current wpa_supplicant.conf
        subprocess.run(["cp", WPA_SUPPLICANT_CONF, f"{WPA_SUPPLICANT_CONF}.bak"], check=True)
        # Append the new network configuration
        with open(WPA_SUPPLICANT_CONF, "a") as wpa_conf:
            wpa_conf.write(f'\nnetwork={{\n    ssid="{ssid}"\n    psk="{psk}"\n}}\n')

    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error configuring Wi-Fi: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure Wi-Fi: {e}")
    except Exception as e:
        logger.error(f"General error configuring Wi-Fi: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure Wi-Fi: {e}")


@router.post("/configure_wifi")
async def configure_wifi(ssid: str = Form(...), password: str = Form(...)):
    try:
        update_wpa_supplicant(ssid, password)
        return {
            "status": "success",
            "message": "Wi-Fi configuration updated. Please manually restart the Raspberry Pi to apply the changes.",
        }
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}
