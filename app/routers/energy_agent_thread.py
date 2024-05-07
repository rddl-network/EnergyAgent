import asyncio
import logging
from fastapi import APIRouter

from app.energy_agent.energy_agent import DataAgent

logger = logging.getLogger(__name__)


class EnergyAgentManager:
    def __init__(self):
        self.agent = DataAgent()
        self.task = None

    def is_running(self):
        return self.task is not None and not self.task.done()

    async def start(self):
        if not self.is_running():
            self.agent.setup()
            self.task = asyncio.create_task(self.agent.run())
            logger.info("Async data agent started")
        else:
            logger.info("Async data agent is already running")

    async def stop(self):
        if self.is_running():
            self.agent.stopped = True
            await self.task
            logger.info("Async data agent stopped")
        else:
            logger.info("Async data agent is not running")

    async def restart(self):
        await self.stop()
        await self.start()

    def get_status(self):
        return "running" if self.is_running() else "stopped"


# FastAPI Router Setup
router = APIRouter(
    prefix="/energy_agent",
    tags=["energy_agent"],
    responses={404: {"detail": "Not found"}},
)

manager = EnergyAgentManager()


@router.get("/start")
async def start_data_agent():
    await manager.start()
    return {"status": manager.get_status()}


@router.get("/stop")
async def stop_data_agent():
    await manager.stop()
    return {"status": manager.get_status()}


@router.get("/status")
async def data_agent_status():
    return {"status": manager.get_status()}


@router.get("/restart")
async def restart_data_agent():
    await manager.restart()
    return {"status": manager.get_status()}
