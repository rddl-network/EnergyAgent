from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="",
    tags=["html"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Home"})


@router.get("/trust-wallet")
async def trust_wallet(request: Request):
    return templates.TemplateResponse("TrustWallet.html", {"request": request, "title": "Trust Wallet"})


@router.get("/smart-meter-page")
async def create_der_smart_meter(request: Request):
    return templates.TemplateResponse("SmartMeterConfig.html", {"request": request})


@router.get("/mqtt-page")
async def mqtt_page(request: Request):
    return templates.TemplateResponse(
        "MqttConfig.html",
        {"request": request, "title": "Configure Shelly and Tasmota Devices"},
    )


@router.get("/cid-page")
async def cid_page(request: Request):
    return templates.TemplateResponse(
        "CIDResolver.html",
        {"request": request, "title": "Local CID Resolver"},
    )


@router.get("/rddl-page")
async def rddl_page(request: Request):
    return templates.TemplateResponse("RddlNetwork.html", {"request": request, "title": "RDDL Network participation"})


@router.get("/create-account")
async def create_account_page(request: Request):
    return templates.TemplateResponse("CreateAccount.html", {"request": request, "title": "Create On Chain Account"})


@router.get("/recover-mnemonic")
async def recover_mnemonic_page(request: Request):
    return templates.TemplateResponse("RecoverMnemonic.html", {"request": request, "title": "Recover Mnemonic"})


@router.get("/create-mnemonic")
async def create_mnemonic_page(request: Request):
    return templates.TemplateResponse("CreateMnemonic.html", {"request": request, "title": "Create Mnemonic"})


@router.get("/activities-page")
async def activities_page(request: Request):
    return templates.TemplateResponse("Activities.html", {"request": request, "title": "RDDL Network Activities"})


@router.get("/smd-entries")
async def smd_entries_page(request: Request):
    return templates.TemplateResponse("SmdEntries.html", {"request": request, "title": "SMD Entries"})


@router.get("/smd-cids/{client_id}")
async def smd_cids_page(request: Request, client_id: str):
    return templates.TemplateResponse(
        "SmdCidTable.html",
        {"request": request, "title": "SMD CIDs", "client_id": client_id},
    )


@router.get("/cid-content/{cid}")
async def cid_content_page(request: Request, cid: str):
    return templates.TemplateResponse("CidData.html", {"request": request, "cid": cid, "title": "CID Content"})


@router.get("/claim-rewards")
async def claim_rewards_page(request: Request):
    return templates.TemplateResponse("ClaimRewards.html", {"request": request, "title": "Claim Rewards"})


@router.get("/logs-page")
async def logs_page(request: Request):
    return templates.TemplateResponse("EnergyAgentLogs.html", {"request": request})


@router.get("/stats-page")
async def stats_page(request: Request):
    return templates.TemplateResponse("EnergyAgentStats.html", {"request": request})


@router.get("/grid")
async def smartmeter_config_page(request: Request):
    return templates.TemplateResponse("SmartMeterConfig.html", {"request": request})

@router.get("/reporting")
async def reporting_page(request: Request):
    return templates.TemplateResponse("Reporting.html", {"request": request})
