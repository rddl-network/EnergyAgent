import logging
import os
import time

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.dependencies import ensure_database
from app.energy_meter_interaction.energy_fetcher import DataFetcher
from app.routers import thing_router, time_series_data_router

app = FastAPI()

# Wait until database is up and running
while True:
    try:
        ensure_database()
        break
    except Exception as e:
        print(e)
        print("Database seems to be down or initializing. Retrying in 5 seconds...")
        time.sleep(5)


origins_list = os.getenv("ORIGINS")
origins = (
    origins_list.split(",")
    if origins_list
    else [
        "http://localhost:3000",
        "https://app-development.r3c.dev:443",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(thing_router)
app.include_router(time_series_data_router)

logging.basicConfig(filename="output.log", level=logging.DEBUG)

# Create DataFetcher object and start thread
data_fetcher = DataFetcher()


@app.on_event("startup")
async def start_data_fetcher():
    await data_fetcher.fetch_data()
