# HealthBooking

Mini-app đặt lịch khám đơn giản, chạy bằng FastAPI. Backend API và UI cơ bản nằm chung trong `main.py`.

## Chạy bằng Git Bash

```bash
cd /d/CODE/AITHUCCHIEN/miniapp/HealthBooking
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8502
```

Mở:

- UI: <http://127.0.0.1:8502/>
- Swagger: <http://127.0.0.1:8502/docs>
- Health: <http://127.0.0.1:8502/health>

## Thông tin đăng ký Super App

- `service_code`: `HEALTH_BOOKING`
- `name`: `Health Booking`
- `category`: `HEALTHCARE`
- `base_url`: `http://localhost:8502`
- `health_check_url`: `http://localhost:8502/health`

Endpoint chính:

- `GET /doctors` - tìm bác sĩ
- `GET /slots` - tìm ca khám còn chỗ
- `POST /bookings` - đặt lịch khám, yêu cầu `Idempotency-Key`
- `GET /bookings/{booking_id}` - xem lịch khám
- `POST /bookings/{booking_id}/cancel` - hủy lịch, yêu cầu `Idempotency-Key`
- `POST /bookings/{booking_id}/reschedule` - đổi ca, yêu cầu `Idempotency-Key`
