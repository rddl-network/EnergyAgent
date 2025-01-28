import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from apscheduler.triggers.cron import CronTrigger

from app.dependencies import config, trust_wallet_instance, measurement_instance
from app.helpers.config_helper import load_config

from app.services.mqttbroadcast import MQTTBroadcaster
from app.services.smart_meter_manager import SmartMeterManager
from app.energy_agent.smartfox import get_smartfox_energy_production
from app.energy_agent.shellypro3em import get_shelly_pro_3em_energy_production

from app.energy_agent.smart_meter_reader.smart_meter_reader import SmartMeterReader
from app.helpers.config_helper import load_config
from app.helpers.logs import log, logger

from app.dependencies import data_buffer


def broadcast_status():
    keys = trust_wallet_instance.get_planetmint_keys()
    state = measurement_instance.get_state(keys.planetmint_address, None)
    broadcaster = MQTTBroadcaster()
    broadcaster.send_state(state)


def read_smart_meter():
    smart_meter_config = load_config(config.path_to_smart_meter_config)
    manager_instance = SmartMeterManager(smart_meter_config)
    data = manager_instance.read_smart_meter()
    smart_meter = SmartMeterReader(smart_meter_config=smart_meter_config, data_buffer=data_buffer)
    try:
        data = smart_meter.read_meter_data()
        measurement_instance.set_sm_data(data)

    except Exception as e:
        logger.error("Failed to read or send meter data: {str(e)}")


def read_shelly_pro_3em_values():
    if config.production_readout_mode != config.PRODUCTION_READOUT_MODE_SHELLYPRO3EM:
        return
    if config.production_readout_ip == "":
        return
    energy_production = get_shelly_pro_3em_energy_production(config.production_readout_ip)
    measurement_instance.set_abs_production_value(energy_production)


def read_smart_fox_values():
    if config.production_readout_mode != config.PRODUCTION_READOUT_MODE_SMARTFOX:
        return
    if config.production_readout_ip == "":
        return
    energy_production = get_smartfox_energy_production(config.production_readout_ip)
    measurement_instance.set_abs_production_value(energy_production)


def init_scheduler(scheduler: BackgroundScheduler):
    scheduler.add_job(
        read_smart_meter,
        trigger=CronTrigger(minute="*/1"),
        id="mutex_write",
        name="Mutex-protected periodic task",
        replace_existing=True,
    )

    scheduler.add_job(
        broadcast_status,
        trigger=CronTrigger(minute="*/1"),
        id="mutex_read",
        name="Mutex-protected periodic task",
        replace_existing=True,
    )

    scheduler.add_job(
        read_smart_fox_values,
        trigger=CronTrigger(minute="*/1"),
        id="mutex_read",
        name="Mutex-protected periodic task",
        replace_existing=True,
    )

    scheduler.add_job(
        read_shelly_pro_3em_values,
        trigger=CronTrigger(minute="*/1"),
        id="mutex_read",
        name="Mutex-protected periodic task",
        replace_existing=True,
    )
