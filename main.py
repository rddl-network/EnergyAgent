import time

from fastapi import FastAPI
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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/hello/")
async def post_hello(name: str):
    return {"message": f"heast oida {name}"}
