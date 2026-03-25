const API = "http://127.0.0.1:8000";

async function loadRooms() {
    const res = await fetch(`${API}/rooms`);
    const data = await res.json();

    const el = document.getElementById("rooms");
    el.innerHTML = "";

    data.forEach(r => {
        el.innerHTML += `<div class="item">${r.id}: ${r.name}</div>`;
    });
}

async function loadBookings() {
    const res = await fetch(`${API}/bookings`);
    const data = await res.json();

    const el = document.getElementById("bookings");
    el.innerHTML = "";

    data.forEach(b => {
        el.innerHTML += `
            <div class="item">
                ${b.user} → комната ${b.room_id} (${b.time})
                <button onclick="deleteBooking(${b.id})">❌</button>
            </div>
        `;
    });
}

async function book() {
    const user = document.getElementById("user").value;
    const room = document.getElementById("room").value;
    const time = document.getElementById("time").value;

    await fetch(`${API}/book`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            user: user,
            room_id: parseInt(room),
            time: time
        })
    });

    loadBookings();
}

async function deleteBooking(id) {
    await fetch(`${API}/book/${id}`, {
        method: "DELETE"
    });

    loadBookings();
}

loadRooms();
loadBookings();