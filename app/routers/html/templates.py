from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


jinja2_templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="",
    tags=["html"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/")
async def home(request: Request):
    return jinja2_templates.TemplateResponse("index.html", {"request": request})


@router.get("/topics-page")
async def get_der_subscription(request: Request):
    return jinja2_templates.TemplateResponse("TopicSubscription.html", {"request": request})


@router.get("/smart-meter-page")
async def create_der_smart_meter(request: Request):
    return jinja2_templates.TemplateResponse("SmartMeterConfig.html", {"request": request})


@router.get("/resolve-cid-page")
async def resolve_cid(request: Request):
    return jinja2_templates.TemplateResponse("ResolveCid.html", {"request": request})


@router.get("/wallet-interaction-page")
async def wallet_interaction(request: Request):
    return jinja2_templates.TemplateResponse("TrustWalletInteraction.html", {"request": request})


# trust wallet interaction


