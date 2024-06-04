import subprocess
import re

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.dependencies import config

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="",
    tags=["html"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Home"}
    )


@router.get("/trust-wallet")
async def read_root(request: Request):
    return templates.TemplateResponse(
        "TrustWallet.html", {"request": request, "title": "Trust Wallet"}
    )


@router.get("/smart-meter-page")
async def create_der_smart_meter(request: Request):
    return templates.TemplateResponse("SmartMeterConfig.html", {"request": request})


@router.get("/mqtt-page")
async def read_about(request: Request):
    return templates.TemplateResponse(
        "MqttConfig.html",
        {"request": request, "title": "Configure Shelly and Tasmota Devices"},
    )


@router.get("/cid-page")
async def read_about(request: Request):
    return templates.TemplateResponse(
        "CIDResolver.html",
        {"request": request, "title": "Local CID Resolver"},
    )


def scan_wifi_networks():
    result = subprocess.run(["iwlist", "wlan0", "scan"], capture_output=True, text=True)
    networks = re.findall(r'ESSID:"([^"]+)"', result.stdout)
    networks = list(set(networks))
    return networks


@router.get("/wifi-config-page")
async def read_root(request: Request):
    networks = scan_wifi_networks()
    return templates.TemplateResponse(
        "WifiConfig.html", {"request": request, "networks": networks}
    )


@router.get("/rddl-page")
async def read_about(request: Request):
    return templates.TemplateResponse(
        "RddlNetwork.html", {"request": request, "title": "RDDL Network participation"}
    )


@router.get("/create-account")
async def read_about(request: Request):
    return templates.TemplateResponse(
        "CreateAccount.html", {"request": request, "title": "Create On Chain Account"}
    )


@router.get("/recover-mnemonic")
async def read_about(request: Request):
    return templates.TemplateResponse(
        "RecoverMnemonic.html", {"request": request, "title": "Recover Mmenonic"}
    )


@router.get("/create-mnemonic")
async def read_about(request: Request):
    return templates.TemplateResponse(
        "CreateMnemonic.html", {"request": request, "title": "Create Mmenonic"}
    )
