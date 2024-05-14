import subprocess
import re

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

jinja2_templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="",
    tags=["html"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/")
async def home(request: Request):
    return jinja2_templates.TemplateResponse("index.html", {"request": request})


@router.get("/energy-agent")
async def energy_agent(request: Request):
    return jinja2_templates.TemplateResponse("EnergyAgent.html", {"request": request})


@router.get("/smart-meter-page")
async def create_der_smart_meter(request: Request):
    return jinja2_templates.TemplateResponse("SmartMeterConfig.html", {"request": request})


@router.get("/mqtt-page")
async def create_mqtt_config(request: Request):
    return jinja2_templates.TemplateResponse("MqttConfig.html", {"request": request})


@router.get("/resolve-cid-page")
async def resolve_cid(request: Request):
    return jinja2_templates.TemplateResponse("LocalCidResolver.html", {"request": request})


def scan_wifi_networks():
    result = subprocess.run(["iwlist", "wlan0", "scan"], capture_output=True, text=True)
    networks = re.findall(r'ESSID:"([^"]+)"', result.stdout)
    networks = list(set(networks))
    return networks


@router.get("/wifi-config-page")
async def read_root(request: Request):
    networks = scan_wifi_networks()
    return jinja2_templates.TemplateResponse("WifiConfig.html", {"request": request, "networks": networks})
