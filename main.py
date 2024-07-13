from fastapi import FastAPI
from databases import Database
import os

DATABASE_URL = (f"postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@"
                f"{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}")

database = Database(DATABASE_URL)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
