from fastapi import APIRouter

from app.dependencies import config
from app.helpers.config_helper import save_config, load_config
from app.helpers.smart_meter_config import SmartMeterConfig
from app.helpers.topic_config import TopicConfig

router = APIRouter(
    prefix="/config",
    tags=["config"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/topics")
async def get_der_subscription() -> TopicConfig:
    topic_config = load_config(config.path_to_topic_config)
    topic_config_obj = TopicConfig()
    topic_config_obj.topics = topic_config

    if topic_config:
        return topic_config_obj
    return TopicConfig()


@router.post("/topics")
async def create_der_subscription(topic_config: TopicConfig):
    save_config(config.path_to_topic_config, topic_config.__dict__)
    return {"message": "Updated DER topic configuration"}


@router.get("/smart-meter")
async def get_der_smart_meter() -> SmartMeterConfig:
    smart_meter_config = load_config(config.path_to_smart_meter_config)
    smart_meter_config_obj = SmartMeterConfig()
    smart_meter_config_obj.smart_meters = smart_meter_config

    if smart_meter_config:
        return smart_meter_config_obj
    return SmartMeterConfig()


@router.post("/smart-meter")
async def create_der_smart_meter(smart_meter_config: SmartMeterConfig):
    save_config(config.path_to_smart_meter_config, smart_meter_config.__dict__)
    return {"message": "Updated smart meter configuration"}
