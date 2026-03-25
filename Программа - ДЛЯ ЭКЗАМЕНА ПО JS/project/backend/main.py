from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

rooms = [
    {"id": 1, "name": "Переговорка A"},
    {"id": 2, "name": "Переговорка B"}
]

bookings = []
booking_id = 1


class Booking(BaseModel):
    user: str
    room_id: int
    time: str


app.mount("/static", StaticFiles(directory="../frontend"), name="static")


@app.get("/")
def index():
    return FileResponse("../frontend/index.html")


@app.get("/rooms")
def get_rooms():
    return rooms


@app.get("/bookings")
def get_bookings():
    return bookings


@app.post("/book")
def book_room(data: Booking):
    global booking_id

    new_booking = {
        "id": booking_id,
        "user": data.user,
        "room_id": data.room_id,
        "time": data.time
    }

    bookings.append(new_booking)
    booking_id += 1

    return new_booking


@app.delete("/book/{id}")
def delete_booking(id: int):
    for b in bookings:
        if b["id"] == id:
            bookings.remove(b)
            return {"message": "deleted"}

    return {"error": "not found"}