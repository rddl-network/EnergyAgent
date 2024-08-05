from fastapi import APIRouter, Body

from app.dependencies import config
from app.energy_agent.energy_decrypter import LANDIS_GYR, SAGEMCOM
from app.helpers.config_helper import save_config, load_config
from app.helpers.models import MQTTConfig, SmartMeterConfig, LandisGyrConfig, SagemcomConfig

router = APIRouter(
    prefix="/config",
    tags=["config"],
    responses={404: {"detail": "Not found"}},
)


# @router.get("/smart-meter")
# async def get_der_smart_meter() -> SmartMeterConfig:
#     smart_meter_config = load_config(config.path_to_smart_meter_config)
#     smart_meter_config_obj = SmartMeterConfig.model_validate(smart_meter_config)
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
async def create_mqtt_config(mqtt_config: MQTTConfig = Body(...)):
    save_config(config.path_to_mqtt_config, mqtt_config.__dict__)
    return {"message": "Updated MQTT configuration"}


@router.get("/smartmeter/config")
async def get_smartmeter_config():
    return load_config(config.path_to_smart_meter_config)


@router.get("/smartmeter/config/type/{type}")
async def get_smartmeter_config_type(type: str):
    if type == LANDIS_GYR:
        smart_meter_config = LandisGyrConfig()
    elif type == SAGEMCOM:
        smart_meter_config = SagemcomConfig()
    else:
        return {"error": "Invalid type"}

    # getting field names
    fields = get_class_vars(smart_meter_config)

    return fields


def get_class_vars(obj):
    all_fields = {}
    for cls in obj.__class__.mro()[::-1]:
        all_fields.update(cls.__dict__)
    return all_fields


@router.post("/smartmeter/config/landisgyr")
async def create_landisgyr_config(smartmeter_config: LandisGyrConfig = Body(...)):
    save_config(config.path_to_smart_meter_config, smartmeter_config.__dict__)
    return {"message": "Updated smartmeter configuration"}


@router.post("/smartmeter/config/sagemcom")
async def create_sagemcom_config(smartmeter_config: SagemcomConfig = Body(...)):
    save_config(config.path_to_smart_meter_config, smartmeter_config.__dict__)
    return {"message": "Updated smartmeter configuration"}
