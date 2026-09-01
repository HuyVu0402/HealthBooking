# HealthBooking - Thông tin đăng ký Mini App

File này dùng để điền form Partner Registration cho mini-app HealthBooking.

URL production đã deploy:

```text
https://healthbooking.onrender.com
```

## 1. Thông tin cơ bản

| Trường trên form | Giá trị cần điền |
|---|---|
| Mã dịch vụ | `HEALTH_BOOKING` |
| Tên dịch vụ | `Health Booking` |
| Mô tả chi tiết | `Mini-app hỗ trợ tìm bác sĩ theo ID/tên, lấy lịch khám của bác sĩ theo ID/tên, đặt lịch khám (chưa thanh toán), thanh toán trực tuyến, đổi thông tin/ca khám, hủy lịch và lấy thông tin lịch khám bệnh.` |
| Danh mục | `HEALTHCARE` hoặc `Y tế` |
| Base URL API | `https://healthbooking.onrender.com` |
| Health Check URL | `https://healthbooking.onrender.com/health` |
| Dịch vụ nhạy cảm | `Bật` |

## 2. Cấu hình API

Upload file `healthbooking-openapi.json`.

Các endpoint trong spec:

| Method | Endpoint | Operation ID | Mục đích |
|---|---|---|---|
| `GET` | `/health` | `health_booking_status` | Kiểm tra mini-app hoạt động |
| `GET` | `/doctors` | `list_clinic_doctors` | Chức năng 1: Lấy tên/ID theo ID hoặc tên bác sĩ |
| `GET` | `/slots` | `search_clinic_slots` | Chức năng 2: Lấy ra lịch khám của 1 bác sĩ theo ID hoặc tên bác sĩ |
| `POST` | `/bookings` | `create_clinic_booking` | Chức năng 3: Đặt lịch khám (khởi tạo chưa thanh toán) |
| `POST` | `/bookings/{booking_id}/pay` | `pay_clinic_booking` | Luồng Thanh Toán: Xác nhận thanh toán thành công |
| `GET` | `/bookings/{booking_id}` | `get_clinic_booking` | Chức năng 6: Xem thông tin chi tiết lịch khám (Deep Link) |
| `GET` | `/bookings` | `search_clinic_bookings` | Chức năng 6: Tra cứu lịch khám theo SĐT/bệnh nhân |
| `POST` | `/bookings/{booking_id}/cancel` | `cancel_clinic_booking` | Chức năng 5: Hủy lịch khám |
| `POST` | `/bookings/{booking_id}/reschedule` | `reschedule_clinic_booking` | Chức năng 4: Đổi ca khám hoặc thông tin lịch khám |

## 3. Cấu hình AI

| Trường trên form | Giá trị cần điền |
|---|---|
| Deep Link Template | `https://healthbooking.onrender.com/?booking_id={booking_id}` |
| Sample Intents | Xem danh sách bên dưới |

Sample intents đề xuất:

```text
tìm bác sĩ Nguyễn Minh Anh
lấy ra lịch khám của bác sĩ Nguyễn Minh Anh theo tên
tôi muốn đặt lịch khám với bác sĩ Nguyễn Minh Anh
thanh toán tiền lịch khám đã đặt
xác nhận thanh toán lịch khám
đổi thông tin lịch khám đã đặt
chuyển lịch khám sang ca khác
hủy lịch khám bác sĩ
lấy thông tin lịch khám bệnh của tôi
tra cứu lịch khám theo số điện thoại
```
