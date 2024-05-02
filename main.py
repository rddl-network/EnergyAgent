from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.energy_meter_interaction.energy_agent import DataAgent
import uvicorn

from app.routers import templates, configuration, cid_resolver, energy_agent_thread

app = FastAPI(
    title="Rddl Energy Agent",
    description="Set of tools that help to interact with the RDDL Network and offer services that are domain agnostic",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Riddle and code",
        "url": "https://www.riddleandcode.com",
        "email": "abc@riddleandcode.com",
    },
    license_info={
        "name": "W3BS 0.9.0",
        "url": "https://www.riddleandcode.com",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(templates.router)
app.include_router(configuration.router)
app.include_router(cid_resolver.router)
app.include_router(energy_agent_thread.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
