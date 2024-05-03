import threading
import logging
from fastapi import APIRouter

from app.dependencies import config
from app.energy_meter_interaction.energy_agent import DataAgent
from app.helpers.config_helper import load_config
from app.helpers.models import SmartMeterConfig

logger = logging.getLogger(__name__)


class EnergyAgentThread:
    def __init__(self):
        self.thread = None
        self.stop_thread = False
        self.data_fetcher = DataAgent()

    def _run(self):
        self.data_fetcher.setup()
        self.data_fetcher.connect_to_mqtt()

    def _is_thread_running(self):
        return self.thread.is_alive() if self.thread else False

    def start(self):
        if not self._is_thread_running():
            self.stop_thread = False
            self.thread = threading.Thread(target=self._run)
            self.thread.start()
            logger.info("Data fetcher started")
        else:
            logger.info("Data fetcher is already running")

    def stop(self):
        self.stop_thread = True
        if self.thread is not None:
            self.thread.join()
        logger.info("Data fetcher stopped")

    def get_status(self):
        return "running" if self._is_thread_running() else "stopped"


router = APIRouter(
    prefix="/energy_agent",
    tags=["energy_agent"],
    responses={404: {"detail": "Not found"}},
)

agent = EnergyAgentThread()


@router.get("/start")
def start_data_agent():
    agent.start()
    return {"status": agent.get_status()}


@router.get("/stop")
def stop_data_agent():
    agent.stop()
    return {"status": agent.get_status()}


@router.get("/status")
def data_agent_status():
    return {"status": agent.get_status()}


@router.get("/restart")
def restart_data_agent():
    agent.stop()
    agent.start()
    return {"status": agent.get_status()}
