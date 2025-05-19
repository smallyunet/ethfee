# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import gas
from api import events
from scheduler.gas_fetcher import start_scheduler

# Initialize FastAPI application
app = FastAPI()

# Enable CORS to allow frontend requests from localhost:8080
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://ethfee.info", "https://ethfee.info"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(gas.router)
app.include_router(events.router)

# Start background scheduler on application startup
@app.on_event("startup")
def startup_event():
    start_scheduler()

# Health check endpoint
@app.get("/")
def read_root():
    return {"msg": "ethfee backend is alive"}
