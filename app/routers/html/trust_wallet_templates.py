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
    return jinja2_templates.TemplateResponse("trust_wallet/Home.html", {"request": request})


@router.get("/create-mnemonic")
async def get_der_subscription(request: Request):
    return jinja2_templates.TemplateResponse("trust_wallet/CreateMnemonic.html", {"request": request})


@router.get("/recover-mnemonic")
async def create_der_smart_meter(request: Request):
    return jinja2_templates.TemplateResponse("trust_wallet/RecoverMnemonic.html", {"request": request})

@router.get("/create-account")
async def create_der_smart_meter(request: Request):
    return jinja2_templates.TemplateResponse("trust_wallet/CreateAccount.html", {"request": request})
