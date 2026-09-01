# Health Booking — Hướng dẫn Mini-app đăng ký lịch khám & Thanh toán

## 1. Tổng quan

**Health Booking** là mini-app demo tích hợp Super App hỗ trợ đầy đủ 6 chức năng cơ bản và luồng thanh toán / Deep Link:

- **Chức năng 1**: Lấy tên/ID theo ID hoặc tên bác sĩ (`GET /doctors`).
- **Chức năng 2**: Lấy ra lịch khám của 1 bác sĩ theo ID hoặc tên bác sĩ (`GET /slots`).
- **Chức năng 3**: Đặt lịch khám theo bác sĩ (`POST /bookings` -> trạng thái `PENDING_PAYMENT` - Đặt thành công chưa thanh toán).
- **Luồng Thanh Toán & Deep Link**:
  - Khi mở Deep Link (`/?booking_id={booking_id}`) hoặc vừa đặt lịch xong, ứng dụng hiển thị giao diện **"Đặt lịch thành công - Chưa thanh toán"** với nút **"Thanh toán ngay"**.
  - Khi bấm nút hoặc nhận callback thông báo thanh toán thành công (`POST /bookings/{booking_id}/pay`), trạng thái chuyển sang **"Thanh toán thành công"** (`PAID`).
- **Chức năng 4**: Đổi thông tin lịch khám (`POST /bookings/{booking_id}/reschedule`).
- **Chức năng 5**: Hủy lịch khám (`POST /bookings/{booking_id}/cancel`).
- **Chức năng 6**: Lấy thông tin lịch khám bệnh (`GET /bookings/{booking_id}` và `GET /bookings`).

---

## 2. Trạng thái Lịch Khám & Giao diện

| Trạng thái | Tên hiển thị trên UI | Mô tả |
|---|---|---|
| `PENDING_PAYMENT` | Đặt thành công - Chưa thanh toán | Mới đặt lịch hoặc mở Deep Link, có nút **"Thanh toán ngay"** |
| `PAID` | Thanh toán thành công | Đã hoàn tất thanh toán tiền khám |
| `CANCELLED` | Đã hủy lịch | Người dùng đã hủy lịch khám |

---

## 3. Danh sách API

| Method | Endpoint | Chức năng | HITL |
|---|---|---|---|
| `GET` | `/health` | Kiểm tra trạng thái mini-app | Không |
| `GET` | `/doctors` | **Chức năng 1**: Lấy tên/ID theo ID hoặc tên bác sĩ | Không |
| `GET` | `/slots` | **Chức năng 2**: Lấy ra lịch khám của bác sĩ theo ID hoặc tên | Không |
| `POST` | `/bookings` | **Chức năng 3**: Đặt lịch khám (Trạng thái `PENDING_PAYMENT`) | Có |
| `POST` | `/bookings/{booking_id}/pay` | **Thanh Toán**: Xác nhận thanh toán (Chuyển sang `PAID`) | Có |
| `POST` | `/bookings/{booking_id}/reschedule` | **Chức năng 4**: Đổi thông tin/ca khám | Có |
| `POST` | `/bookings/{booking_id}/cancel` | **Chức năng 5**: Hủy lịch khám | Có |
| `GET` | `/bookings/{booking_id}` | **Chức năng 6**: Lấy chi tiết lịch khám (Deep Link) | Không |
| `GET` | `/bookings` | **Chức năng 6**: Tra cứu lịch khám theo SĐT/Bệnh nhân | Không |

---

## 4. Hướng dẫn chạy và Test

```bash
# Chạy server Uvicorn
python -m uvicorn main:app --host 127.0.0.1 --port 8502 --reload

# Chạy test suite
pytest tests/test_app.py -v
```

Các URL chính:
- Giao diện Web: <http://127.0.0.1:8502/>
- Deep Link Demo: <http://127.0.0.1:8502/?booking_id=CLB-xxx>
- Swagger UI: <http://127.0.0.1:8502/docs>
- OpenAPI JSON: <http://127.0.0.1:8502/openapi.json>
