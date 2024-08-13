from fastapi import APIRouter, Body

from app.dependencies import config
from app.helpers.config_helper import save_config, load_config, remove_config
from app.helpers.models import MQTTConfig, LandisGyrConfig, SagemcomConfig, LANDIS_GYR, SAGEMCOM

router = APIRouter(
    prefix="/config",
    tags=["config"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/mqtt")
async def get_mqtt_config():
    mqtt_config = load_config(config.path_to_mqtt_config)
    return mqtt_config


@router.post("/mqtt")
async def create_mqtt_config(mqtt_config: MQTTConfig = Body(...)):
    save_config(config.path_to_mqtt_config, mqtt_config.__dict__)
    return {"message": "Updated MQTT configuration"}


@router.get("/smartmeter")
async def get_smartmeter_config():
    return load_config(config.path_to_smart_meter_config)


@router.get("/smartmeter/type/{type}")
async def get_smartmeter_config_type(type: str):
    if type == LANDIS_GYR:
        smart_meter_config = LandisGyrConfig()
    elif type == SAGEMCOM:
        smart_meter_config = SagemcomConfig()
    else:
        return {"error": "Invalid type"}

    config_dict = {key: value for key, value in smart_meter_config.__dict__.items()}

    return config_dict


@router.post(f"/smartmeter/{LANDIS_GYR}")
async def route_create_landisgyr_config(smartmeter_config: LandisGyrConfig = Body(...)):
    save_config(config.path_to_smart_meter_config, smartmeter_config.__dict__)
    return {"message": "Updated smartmeter configuration"}


@router.post(f"/smartmeter/{SAGEMCOM}")
async def route_create_sagemcom_config(smartmeter_config: SagemcomConfig = Body(...)):
    save_config(config.path_to_smart_meter_config, smartmeter_config.__dict__)
    return {"message": "Updated smartmeter configuration"}


@router.delete("/smartmeter")
async def route_delete_smartmeter_config():
    remove_config(config.path_to_smart_meter_config)
    return {"message": "Updated smartmeter configuration"}


@router.get("/smartmeter/mqtt")
async def route_get_mqtt_config():
    mqtt_config = load_config(config.path_to_smart_meter_mqtt_config)
    return mqtt_config


@router.post("/smartmeter/mqtt")
async def route_create_mqtt_config(mqtt_config: MQTTConfig = Body(...)):
    save_config(config.path_to_smart_meter_mqtt_config, mqtt_config.__dict__)
    return {"message": "Updated MQTT configuration"}
