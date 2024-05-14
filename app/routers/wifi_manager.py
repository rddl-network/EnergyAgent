import subprocess
import re

from fastapi import APIRouter, Form

router = APIRouter(
    prefix="/wifi",
    tags=["wifi"],
    responses={404: {"detail": "Not found"}},
)


@router.post("/configure_wifi/")
async def configure_wifi(ssid: str = Form(...), password: str = Form(...)):
    try:
        config = f"""
        network={{
            ssid="{ssid}"
            psk="{password}"
        }}
        """
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "a") as file:
            file.write(config)
        subprocess.run(["sudo", "systemctl", "restart", "dhcpcd"])
        return {"status": "success", "message": "Wi-Fi configuration updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
