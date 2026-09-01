# HealthBooking

Mini-app đặt lịch khám bệnh tích hợp Super App, hỗ trợ 6 chức năng cơ bản, luồng thanh toán và giao diện Deep Link. Backend API và UI demo chạy bằng FastAPI trong `main.py`.

## Các chức năng chính & Luồng Thanh Toán

1. **Lấy tên/ID theo ID hoặc tên bác sĩ**: `GET /doctors`
2. **Lấy ra lịch khám của 1 bác sĩ theo ID hoặc theo tên**: `GET /slots`
3. **Đặt lịch khám theo bác sĩ**: `POST /bookings` (Trạng thái ban đầu: `PENDING_PAYMENT` - Đặt thành công chưa thanh toán)
4. **Luồng Thanh Toán / Deep Link**:
   - Truy cập Deep Link `/?booking_id={booking_id}` hiển thị màn hình **"Đặt lịch thành công - Chưa thanh toán"** kèm nút **"Thanh toán ngay"**.
   - Ấn nút hoặc nhận callback `POST /bookings/{booking_id}/pay` chuyển trạng thái sang **"Thanh toán thành công"** (`PAID`).
5. **Đổi thông tin của lịch khám đó**: `POST /bookings/{booking_id}/reschedule`
6. **Hủy lịch khám**: `POST /bookings/{booking_id}/cancel`
7. **Lấy thông tin lịch khám bệnh**: `GET /bookings/{booking_id}` & `GET /bookings`

## Chạy ứng dụng

```bash
cd /d/CODE/AITHUCCHIEN/miniapp/HealthBooking
python -m uvicorn main:app --host 127.0.0.1 --port 8502
```

Chạy test suite:

```bash
pytest tests/test_app.py -v
```

Mở:

- UI Demo: <http://127.0.0.1:8502/>
- Deep Link Demo: <http://127.0.0.1:8502/?booking_id=CLB-xxx>
- Swagger UI: <http://127.0.0.1:8502/docs>
- Health check: <http://127.0.0.1:8502/health>
- OpenAPI JSON: <http://127.0.0.1:8502/openapi.json>
