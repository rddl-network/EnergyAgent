from xml.etree.ElementTree import ParseError
from apscheduler.schedulers.background import BackgroundScheduler

from apscheduler.triggers.cron import CronTrigger

from app.dependencies import (
    config,
    trust_wallet_instance,
    measurement_instance,
    PRODUCTION_READOUT_MODE_SHELLYPRO3EM,
    PRODUCTION_READOUT_MODE_SMARTFOX,
)
from app.helpers.config_helper import load_config

from app.services.mqttbroadcast import MQTTBroadcaster
from app.energy_agent.smartfox import get_smartfox_energy_production
from app.energy_agent.shellypro3em import get_shelly_pro_3em_energy_production

from app.energy_agent.smart_meter_reader.smart_meter_reader import SmartMeterReader
from app.helpers.config_helper import load_config
from app.helpers.logs import logger

from app.dependencies import data_buffer


def broadcast_status():
    keys = trust_wallet_instance.get_planetmint_keys()
    state = measurement_instance.get_state(keys.planetmint_address, None)
    broadcaster = MQTTBroadcaster()
    broadcaster.send_state(state)


def read_smart_meter():
    smart_meter_config = load_config(config.path_to_smart_meter_config)
    smart_meter = SmartMeterReader(smart_meter_config=smart_meter_config, data_buffer=data_buffer)
    try:
        data = smart_meter.read_meter_data()
        if data:
            measurement_instance.set_sm_data(data)
    except ParseError as e:
        logger.error(f"Failed to parse extracted data {str(e)}")
    except Exception as e:
        logger.error(f"Failed to read or send meter data: {str(e)}")


def read_shelly_pro_3em_values():
    if config.production_readout_mode != PRODUCTION_READOUT_MODE_SHELLYPRO3EM:
        return
    if config.production_readout_ip == "":
        return
    energy_production = get_shelly_pro_3em_energy_production(config.production_readout_ip)
    measurement_instance.set_abs_production_value(energy_production)


def read_smart_fox_values():
    if config.production_readout_mode != PRODUCTION_READOUT_MODE_SMARTFOX:
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
        name="Read Smart Meter",
        replace_existing=True,
    )

    scheduler.add_job(
        broadcast_status,
        trigger=CronTrigger(minute="*/1"),
        id="mutex_read",
        name="Report State",
        replace_existing=True,
    )

    scheduler.add_job(
        read_smart_fox_values,
        trigger=CronTrigger(minute="*/1"),
        id="mutex_read",
        name="Read from smartfox",
        replace_existing=True,
    )

    scheduler.add_job(
        read_shelly_pro_3em_values,
        trigger=CronTrigger(minute="*/1"),
        id="mutex_read",
        name="Read Shelly Pro 3 EM",
        replace_existing=True,
    )
