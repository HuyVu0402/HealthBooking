from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["service_code"] == "HEALTH_BOOKING"


def test_list_doctors_and_slots():
    doctors = client.get("/doctors").json()["data"]["doctors"]
    assert len(doctors) >= 4

    doctor_id = doctors[0]["doctor_id"]
    slots = client.get("/slots", params={"doctor_id": doctor_id, "available_only": True}).json()["data"]["slots"]
    assert slots
    assert slots[0]["doctor_id"] == doctor_id
    assert slots[0]["available"] is True


def test_create_booking_is_idempotent():
    doctor_id = "DOC-NOI-01"
    slot_id = client.get("/slots", params={"doctor_id": doctor_id, "available_only": True}).json()["data"]["slots"][0]["slot_id"]
    payload = {
        "doctor_id": doctor_id,
        "slot_id": slot_id,
        "patient_name": "Nguyen Van A",
        "patient_phone": "0912345678",
        "reason": "Kham suc khoe tong quat",
    }
    headers = {"Idempotency-Key": "test-health-booking-create"}

    first = client.post("/bookings", json=payload, headers=headers)
    second = client.post("/bookings", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["booking"]["booking_id"] == second.json()["data"]["booking"]["booking_id"]


def test_openapi_has_hitl_metadata():
    spec = client.get("/openapi.json").json()
    operation = spec["paths"]["/bookings"]["post"]
    assert operation["operationId"] == "create_clinic_booking"
    assert operation["x-requires-hitl"] is True
    assert operation["x-idempotency-required"] is True
