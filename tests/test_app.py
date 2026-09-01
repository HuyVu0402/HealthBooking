from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["service_code"] == "HEALTH_BOOKING"


def test_feature_1_get_doctor_by_id_or_name():
    # 1. Lấy tên/id theo id/tên bác sĩ
    # Theo tên bác sĩ
    res_name = client.get("/doctors", params={"name": "Nguyễn Minh Anh"}).json()
    assert res_name["status"] == "success"
    assert len(res_name["data"]["doctors"]) == 1
    assert res_name["data"]["doctors"][0]["doctor_id"] == "DOC-NOI-01"

    # Theo ID bác sĩ
    res_id = client.get("/doctors", params={"doctor_id": "DOC-NHI-01"}).json()
    assert res_id["status"] == "success"
    assert len(res_id["data"]["doctors"]) == 1
    assert res_id["data"]["doctors"][0]["name"] == "BS. Trần Thu Hà"


def test_feature_2_get_slots_by_doctor_id_or_name():
    # 2. Lấy ra lịch khám của 1 bác sĩ theo id hoặc theo tên
    # Theo tên bác sĩ
    res_name = client.get("/slots", params={"doctor_name": "Nguyễn Minh Anh", "available_only": True}).json()
    assert res_name["status"] == "success"
    assert len(res_name["data"]["slots"]) > 0
    assert res_name["data"]["slots"][0]["doctor_id"] == "DOC-NOI-01"

    # Theo ID bác sĩ
    res_id = client.get("/slots", params={"doctor_id": "DOC-MAT-01", "available_only": True}).json()
    assert res_id["status"] == "success"
    assert len(res_id["data"]["slots"]) > 0
    assert res_id["data"]["slots"][0]["doctor_id"] == "DOC-MAT-01"


def test_feature_3_4_5_6_and_payment_flow():
    # 3. Đặt lịch khám theo bác sĩ (Khởi tạo PENDING_PAYMENT - Đặt thành công nhưng chưa thanh toán)
    slots = client.get("/slots", params={"doctor_id": "DOC-NOI-01", "available_only": True}).json()["data"]["slots"]
    slot_1 = slots[0]["slot_id"]
    slot_2 = slots[1]["slot_id"]

    payload = {
        "doctor_id": "DOC-NOI-01",
        "slot_id": slot_1,
        "patient_name": "Nguyen Van Test",
        "patient_phone": "0912345678",
        "reason": "Kham suc khoe tong quat",
    }
    headers = {"Idempotency-Key": "test-flow-payment-001"}

    create_res = client.post("/bookings", json=payload, headers=headers)
    assert create_res.status_code == 200
    create_body = create_res.json()
    assert create_body["status"] == "success"

    # Kiểm tra operation_id chuẩn SDK (chữ thường)
    op_id = create_body["operation_id"]
    assert op_id.startswith("health-booking-clb-")
    assert op_id.islower()

    booking = create_body["data"]["booking"]
    booking_id = booking["booking_id"]
    assert booking["status"] == "PENDING_PAYMENT"

    # Xử lý Thanh Toán (Chuyển PENDING_PAYMENT -> PAID)
    pay_res = client.post(f"/bookings/{booking_id}/pay", json={"payment_method": "SUPERAPP_PAY"}, headers={"Idempotency-Key": "test-pay-001"}).json()
    assert pay_res["status"] == "success"
    paid_booking = pay_res["data"]["booking"]
    assert paid_booking["status"] == "PAID"
    assert "paid_at" in paid_booking
    assert pay_res["operation_id"].startswith("health-payment-clb-")

    # 6. Lấy thông tin lịch khám bệnh
    get_res = client.get(f"/bookings/{booking_id}").json()
    assert get_res["status"] == "success"
    assert get_res["data"]["booking"]["status"] == "PAID"

    # 4. Đổi thông tin của lịch khám đó
    reschedule_payload = {
        "new_slot_id": slot_2,
        "patient_name": "Nguyen Van Test Updated",
        "patient_phone": "0987654321",
        "reason": "Doi sang kham buoi chieu",
    }
    reschedule_res = client.post(f"/bookings/{booking_id}/reschedule", json=reschedule_payload, headers={"Idempotency-Key": "test-reschedule-001"}).json()
    assert reschedule_res["status"] == "success"
    updated_booking = reschedule_res["data"]["booking"]
    assert updated_booking["slot_id"] == slot_2
    assert updated_booking["patient_name"] == "Nguyen Van Test Updated"

    # 5. Hủy lịch khám
    cancel_res = client.post(f"/bookings/{booking_id}/cancel", json={"reason": "Ban viec dot xuat"}, headers={"Idempotency-Key": "test-cancel-001"}).json()
    assert cancel_res["status"] == "success"
    assert cancel_res["data"]["booking"]["status"] == "CANCELLED"


def test_openapi_has_hitl_metadata():
    spec = client.get("/openapi.json").json()
    operation = spec["paths"]["/bookings"]["post"]
    assert operation["operationId"] == "create_clinic_booking"
    assert operation["x-requires-hitl"] is True
    assert operation["x-idempotency-required"] is True

    pay_op = spec["paths"]["/bookings/{booking_id}/pay"]["post"]
    assert pay_op["operationId"] == "pay_clinic_booking"
    assert pay_op["x-requires-hitl"] is True
