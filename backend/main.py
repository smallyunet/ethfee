# backend/main.py
from fastapi import FastAPI
from api import gas

app = FastAPI()
app.include_router(gas.router)

@app.get("/")
def read_root():
    return {"msg": "ethfee backend is alive"}
