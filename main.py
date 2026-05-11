from fastapi import FastAPI
from app.config import get_db, engine, Base
from app.models import Event

# Khởi tạo các bảng trong Database nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Management System API")

@app.get("/api/events")
def get_events():
    with get_db() as db:
        events = db.query(Event).all()
        events_data = []
        for event in events:
            events_data.append({
                "id": event.event_id,
                "name": event.event_name,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "status": event.status,
                "max_capacity": event.max_capacity
            })
        return {"status": "success", "data": events_data}