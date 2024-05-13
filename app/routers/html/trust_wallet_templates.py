from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.dependencies import config

jinja2_templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="",
    tags=["html"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/trust-wallet")
async def twi(request: Request):
    return jinja2_templates.TemplateResponse("trust_wallet/Home.html", {"request": request, "api_port": config.port})


@router.get("/create-mnemonic")
async def get_der_subscription(request: Request):
    return jinja2_templates.TemplateResponse("trust_wallet/CreateMnemonic.html",
                                             {"request": request, "api_port": config.port})


@router.get("/recover-mnemonic")
async def create_der_smart_meter(request: Request):
    return jinja2_templates.TemplateResponse("trust_wallet/RecoverMnemonic.html",
                                             {"request": request, "api_port": config.port})
