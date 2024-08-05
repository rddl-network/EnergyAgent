from fastapi import APIRouter, Depends, HTTPException
import asyncio

from app.RddlInteraction.TrustWallet.osc_message_sender import is_not_connected
from app.dependencies import config, data_buffer
from app.energy_agent.energy_agent import EnergyAgent
from app.helpers.config_helper import load_config, save_config
from app.helpers.logs import log, logger

_manager_instance = None

METADATA_CONFIG_PATH = config.config_base_path + "/energy_agent_metadata.json"


class EnergyAgentManager:
    def __init__(self):
        self.energy_agent = None
        self.task = None
        loaded_status = load_config(METADATA_CONFIG_PATH).get("status")
        if loaded_status == "":
            loaded_status = "stopped"
        self.status = loaded_status

    @log
    def is_running(self):
        if self.task is None:
            return False
        if not self.task.done():
            return True
        exception = self.task.exception()
        if exception:
            logger.error(f"Task ended with exception: {exception}")
        return False

    @log
    async def start(self):
        if not self.is_running():
            self.energy_agent = EnergyAgent(data_buffer)
            self.energy_agent.setup()
            self.task = asyncio.create_task(self.energy_agent.run())
            self.status = "running"
            save_config(METADATA_CONFIG_PATH, {"status": self.status})
            logger.info("Async data agent started")
        else:
            logger.info("Async data agent is already running")

    @log
    async def await_and_stop(self, update_status=True):
        if self.is_running():
            self.energy_agent.stopped = True
            await self.task
            await self.energy_agent.disconnect_from_mqtt()
            self.energy_agent = None
            if update_status:
                self.status = "stopped"
                save_config(METADATA_CONFIG_PATH, {"status": self.status})
            logger.info("Async data agent stopped")
        else:
            logger.info("Async data agent is not running")

    @log
    async def restart(self):
        await self.await_and_stop()
        await self.start()

    @log
    def get_status(self):
        if self.is_running():
            return "running"
        return "stopped"

    @log
    async def check_and_restart(self):
        if self.status == "running" and not self.is_running():
            await self.start()


@log
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
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
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
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    await manager.restart()
    return {"status": manager.get_status()}
