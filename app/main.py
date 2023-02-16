import time

from fastapi import FastAPI

from app.dependencies import ensure_database
from app.routers import machine_router, time_series_data_router

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


app.include_router(time_series_data_router)
app.include_router(machine_router)
