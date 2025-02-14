from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.energy_agent.shellypro3em import read_shelly_pro_3em_values
from app.energy_agent.smartfox import read_smart_fox_values
from app.energy_agent.smart_meter_reader.smart_meter_reader import read_smart_meter

from app.services.mqtt_reporter import broadcast_status


def init_scheduler(scheduler: BackgroundScheduler):
    scheduler.add_job(
        read_smart_meter,
        trigger=CronTrigger(minute="*/15"),
        id="read_smart_meter",
        name="Read Smart Meter",
        replace_existing=True,
    )

    scheduler.add_job(
        broadcast_status,
        trigger=CronTrigger(minute="*/15"),
        id="mqtt_reporter",
        name="Report State",
        replace_existing=True,
    )

    scheduler.add_job(
        read_smart_fox_values,
        trigger=CronTrigger(minute="*/15"),
        id="read_smart_fox",
        name="Read from smartfox",
        replace_existing=True,
    )

    scheduler.add_job(
        read_shelly_pro_3em_values,
        trigger=CronTrigger(minute="*/15"),
        id="read_shellypro3em",
        name="Read Shelly Pro 3 EM",
        replace_existing=True,
    )
