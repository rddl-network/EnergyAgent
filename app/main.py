import time

from fastapi import FastAPI

from app.dependencies import ensure_database, config
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


app.include_router(thing_router)
app.include_router(time_series_data_router)

data_fetcher = DataFetcher(config.data_fetcher_interval)
data_fetcher.start()
