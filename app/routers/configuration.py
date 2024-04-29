from fastapi import APIRouter

from app.dependencies import config
from app.helpers.config_helper import save_config, load_config
from app.helpers.models import SmartMeterConfig, TopicConfig

router = APIRouter(
    prefix="/config",
    tags=["config"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/topics")
async def get_der_subscription() -> TopicConfig | dict:
    topic_config_dict = load_config(config.path_to_topic_config)
    if not topic_config_dict:
        return TopicConfig()
    topic_config = TopicConfig.parse_obj(topic_config_dict)
    return topic_config


@router.post("/topics")
async def create_der_subscription(topic_config: TopicConfig):
    save_config(config.path_to_topic_config, topic_config.__dict__)
    return {"message": "Updated Smart Metering device topic configuration"}


@router.get("/smart-meter")
async def get_der_smart_meter() -> SmartMeterConfig:
    smart_meter_config = load_config(config.path_to_smart_meter_config)
    smart_meter_config_obj = SmartMeterConfig.parse_obj(smart_meter_config)

    if smart_meter_config:
        return smart_meter_config_obj
    return SmartMeterConfig()


@router.post("/smart-meter")
async def create_der_smart_meter(smart_meter_config: SmartMeterConfig):
    save_config(config.path_to_smart_meter_config, smart_meter_config.__dict__)
    return {"message": "Updated smart meter configuration"}
