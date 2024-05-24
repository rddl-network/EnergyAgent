from fastapi import APIRouter, Form, HTTPException
import logging
from wifi import Cell, Scheme

router = APIRouter(
    prefix="/wifi",
    tags=["wifi"],
    responses={404: {"detail": "Not found"}},
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

WPA_SUPPLICANT_CONF = "/etc/wpa_supplicant/wpa_supplicant.conf"


def configure_wifi_with_wifi_package(ssid: str, psk: str):
    try:
        cells = Cell.all('wlan0')
        target_cell = next((cell for cell in cells if cell.ssid == ssid), None)
        if target_cell is None:
            raise HTTPException(status_code=404, detail=f"SSID '{ssid}' not found.")

        scheme = Scheme.for_cell('wlan0', 'home', target_cell, psk)
        scheme.save()
        scheme.activate()
    except Exception as e:
        logger.error(f"Error configuring Wi-Fi: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure Wi-Fi: {e}")


@router.post("/configure_wifi")
async def configure_wifi(ssid: str = Form(...), password: str = Form(...)):
    try:
        configure_wifi_with_wifi_package(ssid, password)
        return {
            "status": "success",
            "message": "Wi-Fi configuration updated. The connection should be active now.",
        }
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}
