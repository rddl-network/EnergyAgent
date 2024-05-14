import subprocess

from fastapi import APIRouter

router = APIRouter(
    prefix="/wifi",
    tags=["wifi"],
    responses={404: {"detail": "Not found"}},
)


@router.post("/configure_wifi/")
async def configure_wifi(ssid: str, password: str):
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
        return {"status": "Wi-Fi configuration updated"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}
