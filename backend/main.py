from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from routers import buses, events, reports, scanner
from ws.manager import manager
from services.bus_dataset_service import seed_buses_from_dataset

# Auto-create necessary SQLite database schema on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vehitrax AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(buses.router, prefix="/api/buses", tags=["Buses"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["Scanner"])


@app.on_event("startup")
def seed_bus_registry():
    db = SessionLocal()
    try:
        result = seed_buses_from_dataset(db)
        print(
            "Dataset sync:",
            f"inserted={result['inserted']}",
            f"updated={result['updated']}",
            f"skipped={result['skipped']}",
        )
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to Vehitrax AI Backend"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
