# backend/main.py
from fastapi import FastAPI
from api import gas
from api import events 
from scheduler.gas_fetcher import start_scheduler

app = FastAPI()
app.include_router(gas.router)
app.include_router(events.router) 

@app.on_event("startup")
def startup_event():
    start_scheduler()

@app.get("/")
def read_root():
    return {"msg": "ethfee backend is alive"}
