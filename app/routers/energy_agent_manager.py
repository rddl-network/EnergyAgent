from fastapi import APIRouter, Depends
import asyncio
import logging
from app.energy_agent.energy_agent import DataAgent

logger = logging.getLogger(__name__)

_manager_instance = None


class EnergyAgentManager:
    def __init__(self):
        self.data_agent = None
        self.task = None

    def is_running(self):
        if self.task and not self.task.done():
            return True
        if self.task:
            if self.task.exception():
                logger.error(f"Task ended with exception: {self.task.exception()}")
            else:
                logger.info("Task completed successfully.")
        return False

    async def start(self):
        if not self.is_running():
            self.data_agent = DataAgent()
            self.data_agent.setup()
            self.task = asyncio.create_task(self.data_agent.run())
            logger.info("Async data agent started")
        else:
            logger.info("Async data agent is already running")

    async def await_and_stop(self):
        if self.is_running():
            self.data_agent.stopped = True
            await self.task
            await self.data_agent.disconnect_from_mqtt()
            self.data_agent = None
            logger.info("Async data agent stopped")
        else:
            logger.info("Async data agent is not running")

    async def restart(self):
        await self.await_and_stop()
        await self.start()

    def get_status(self):
        if self.is_running():
            return "running"
        return "stopped"


def get_manager():
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = EnergyAgentManager()
    return _manager_instance


router = APIRouter(
    prefix="/energy_agent",
    tags=["energy_agent"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/start")
async def start_data_agent(manager: EnergyAgentManager = Depends(get_manager)):
    await manager.start()
    return {"status": manager.get_status()}


@router.get("/stop")
async def stop_data_agent(manager: EnergyAgentManager = Depends(get_manager)):
    await manager.await_and_stop()
    return {"status": manager.get_status()}


@router.get("/status")
async def data_agent_status(manager: EnergyAgentManager = Depends(get_manager)):
    return {"status": manager.get_status()}


@router.get("/restart")
async def restart_data_agent(manager: EnergyAgentManager = Depends(get_manager)):
    await manager.restart()
    return {"status": manager.get_status()}
