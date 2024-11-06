import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from starlette.staticfiles import StaticFiles

from app.dependencies import config
from app.helpers.config_helper import load_config
from app.helpers.logs import logger

from app.routers import (
    configuration,
    cid_resolver,
    trust_wallet_interaction,
    manage_smd,
    rddl_network,
    tx_resolver,
    smd_entry,
    energy_agent_logs,
)
from app.services import energy_agent_manager, smart_meter_manager
from app.services.energy_agent_manager import get_energy_agent_manager
from app.routers.html import templates, trust_wallet_templates
from app.RddlInteraction.rddl_client import RDDLAgent
from app.services.smart_meter_manager import get_smart_meter_manager


async def startup_event():
    # Your startup logic here (e.g., database connection)
    ag = RDDLAgent()
    ag.setup()
    await ag.run()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    rddl_task = asyncio.create_task(startup_event())

    energy_manager = get_energy_agent_manager()
    await energy_manager.check_and_restart()

    sm_manager = get_smart_meter_manager()
    await sm_manager.check_and_restart()

    yield  # This is where your application starts handling requests
    print("Shutting down...")

    rddl_task.cancel()
    try:
        await rddl_task
    except asyncio.CancelledError:
        logger.info("RDDL task cancelled")
        pass

    await energy_manager.await_and_stop(update_status=False)


app = FastAPI(
    title="Rddl Energy Agent",
    description="Set of tools that help to interact with the RDDL Network and offer services that are domain agnostic",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This routes the API
app.mount("/static", StaticFiles(directory="app/templates/static"), name="static")

app.include_router(configuration.router)
app.include_router(cid_resolver.router)
app.include_router(energy_agent_manager.router)
app.include_router(trust_wallet_interaction.router)
app.include_router(rddl_network.router)
app.include_router(manage_smd.router)
app.include_router(tx_resolver.router)

# This routes the HTML
app.include_router(templates.router)
app.include_router(trust_wallet_templates.router)
app.include_router(smd_entry.router)
app.include_router(energy_agent_logs.router)
app.include_router(smart_meter_manager.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2138)
