import time

from fastapi import FastAPI

import routers.time_series_data
from dependencies import ensure_database

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


app.include_router(routers.time_series_data_router)
app.include_router(routers.machine_router)
