from fastapi import APIRouter

from app.dependencies import config
from app.helpers.config_helper import save_config, load_config
from app.helpers.models import MQTTConfig

router = APIRouter(
    prefix="/config",
    tags=["config"],
    responses={404: {"detail": "Not found"}},
)


# @router.get("/smart-meter")
# async def get_der_smart_meter() -> SmartMeterConfig:
#     smart_meter_config = load_config(config.path_to_smart_meter_config)
#     smart_meter_config_obj = SmartMeterConfig.parse_obj(smart_meter_config)
#
#     if smart_meter_config:
#         return smart_meter_config_obj
#     return SmartMeterConfig()


# @router.post("/smart-meter")
# async def create_der_smart_meter(smart_meter_config: SmartMeterConfig):
#     save_config(config.path_to_smart_meter_config, smart_meter_config.__dict__)
#     return {"message": "Updated smart meter configuration"}


@router.get("/mqtt")
async def get_mqtt_config():
    mqtt_config = load_config(config.path_to_mqtt_config)
    return mqtt_config


@router.post("/mqtt")
async def create_mqtt_config(mqtt_config: MQTTConfig):
    save_config(config.path_to_mqtt_config, mqtt_config.__dict__)
    return {"message": "Updated MQTT configuration"}
