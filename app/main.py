import os
import sys
import asyncio
from fastapi import FastAPI

# Add project root to sys.path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.routes import router
from app.storage.redis_client import redis_client
from workers.monitor import MonitorWorker

app = FastAPI(title="Security Monitor API")

# Store the background task so it doesn't get swept away
monitor_task = None

@app.on_event("startup")
async def startup_event():
    global monitor_task
    print("[INIT] Starting integrated Security Monitor...")
    worker = MonitorWorker()
    # Run the worker as a background task
    monitor_task = asyncio.create_task(worker.run())

@app.on_event("shutdown")
async def shutdown_event():
    if monitor_task:
        monitor_task.cancel()
    await redis_client.close()

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Security Monitoring & Intrusion Detection API. Visit /docs for more info"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
