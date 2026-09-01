# Tiêu chuẩn SDK Mini App của Super App v1

## 1. Mục tiêu

Tài liệu này là hợp đồng tối thiểu dành cho mọi Mini App được đăng ký vào Super App.
Mini App không được tự tạo response tùy ý nếu response đó được Agent xử lý.

## 2. Nguyên tắc bắt buộc

- Mini App phải có `service_code`, `base_url`, OpenAPI và `operationId` ổn định.
- Mọi thao tác thành công có phát sinh side effect phải trả về `operation_id`.
- `operation_id` phải đại diện cho cùng một nghiệp vụ trong các lần retry.
- Không dùng `request_id`, `task_id` hoặc `thread_id` thay cho `operation_id`.
- ID nghiệp vụ phải nằm trong `data` ở cấp cao nhất.
- Không trả secret, JWT, API key hoặc dữ liệu nội bộ trong response.

## 3. Quy tắc ID theo Agent

### 3.1. `operation_id`

Định dạng:

```text
<domain>-<opaque-id>
```

Quy tắc:

- Chỉ dùng chữ thường và chữ số.
- Bắt đầu bằng chữ cái.
- Phải có dấu gạch ngang ngăn cách domain và opaque ID.
- Độ dài tối đa 128 ký tự.
- Ổn định khi retry cùng một nghiệp vụ.

Ví dụ hợp lệ:

```text
ride-123
payment-123
event-booking-abc123
health-booking-clb-a1b2c3d4
health-payment-clb-a1b2c3d4
```

Ví dụ không hợp lệ:

```text
Ride-123
ride_123
123
ride
```

### 3.2. Các ID liên quan

| Trường | Mục đích | Ví dụ |
|---|---|---|
| `operation_id` | ID nghiệp vụ chính, bắt buộc với mutation thành công | `health-booking-clb-a1b2c3d4` |
| `booking_id` | ID đặt chỗ/đặt lịch | `CLB-A1B2C3D4` |
| `ride_id` | ID chuyến xe | `RIDE-123` |
| `payment_id` | ID giao dịch thanh toán | `PAY-123` |
| `request_id` | ID của một HTTP request | `req-uuid` |
| `event_id` | ID callback/event, dùng để deduplicate | `evt-uuid` |

`request_id`, `event_id` và `operation_id` không được dùng thay thế cho nhau.

## 4. Success response

```json
{
  "status": "success",
  "message": "Đặt lịch khám thành công (Chờ thanh toán)",
  "operation_id": "health-booking-clb-a1b2c3d4",
  "data": {
    "booking": {
      "booking_id": "CLB-A1B2C3D4",
      "status": "PENDING_PAYMENT"
    }
  }
}
```

Với `create`, `update`, `cancel`, `payment` hoặc thao tác có side effect:

- Phải có `operation_id` (chữ thường).
- Phải có ID tài nguyên trong `data`.
- Cùng `Idempotency-Key` và cùng input phải trả về cùng operation.

## 5. Error response

```json
{
  "status": "failure",
  "code": "SLOT_FULL",
  "message": "Ca khám đã hết chỗ",
  "error": {
    "code": "SLOT_FULL",
    "message": "Ca khám đã hết chỗ",
    "details": {}
  }
}
```

Code gợi ý:

| Code | Ý nghĩa |
|---|---|
| `INVALID_REQUEST` | Input không hợp lệ |
| `UNAUTHORIZED` / `INVALID_API_KEY` | Thiếu hoặc sai xác thực API Key |
| `IDEMPOTENCY_KEY_REQUIRED` | Thiếu Idempotency-Key với mutation |
| `DOCTOR_NOT_FOUND` | Không tìm thấy bác sĩ theo ID hoặc tên |
| `INVALID_SLOT` | Ca khám không hợp lệ |
| `SLOT_FULL` | Ca khám đã hết chỗ |
| `BOOKING_NOT_FOUND` | Không tìm thấy lịch khám |
| `BOOKING_CANCELLED` | Lịch đã bị hủy không thể thao tác |
| `INVALID_NEW_SLOT` | Ca mới không hợp lệ hoặc không thuộc cùng bác sĩ |

## 6. Yêu cầu OpenAPI

Mỗi operation phải có `operationId` và bổ sung metadata chuẩn:

```yaml
operationId: create_clinic_booking
x-risk-level: high
x-side-effect-type: mutation
x-requires-hitl: true
x-idempotency-required: true
x-retry-policy: no_retry
```

## 7. Quy chuẩn API Health Booking (6 Chức năng + Luồng Thanh Toán & Deep Link)

### Trạng thái Lịch Khám:
- `PENDING_PAYMENT`: Đặt lịch khám thành công nhưng chưa thanh toán.
- `PAID`: Đã hoàn tất thanh toán (chuyển sang phần thanh toán thành công).
- `CANCELLED`: Đã hủy lịch khám.

### 7.1. Lấy tên/ID theo ID hoặc tên bác sĩ
- **Endpoint**: `GET /doctors`
- **Params**: `doctor_id`, `name`, `specialty`

### 7.2. Lấy ra lịch khám của 1 bác sĩ theo ID hoặc theo tên
- **Endpoint**: `GET /slots`
- **Params**: `doctor_id` hoặc `doctor_name`, `appointment_date`, `available_only`

### 7.3. Đặt lịch khám theo bác sĩ (Khởi tạo Chờ thanh toán)
- **Endpoint**: `POST /bookings` (Yêu cầu `Idempotency-Key`)
- Trả về `booking_id`, trạng thái `PENDING_PAYMENT` và `operation_id = health-booking-<id>`.

### 7.4. Thanh Toán Lịch Khám (Xác nhận chuyển sang Thanh toán thành công)
- **Endpoint**: `POST /bookings/{booking_id}/pay` (Yêu cầu `Idempotency-Key`)
- **Body**: `payment_method` (tùy chọn)
- Dùng khi người dùng bấm nút **"Thanh toán ngay"** trên giao diện HOẶC Super App nhận được thông báo/callback thanh toán thành công.
- Chuyển trạng thái lịch khám từ `PENDING_PAYMENT` sang `PAID`, trả về `operation_id = health-payment-<id>`.

### 7.5. Đổi thông tin của lịch khám đó
- **Endpoint**: `POST /bookings/{booking_id}/reschedule` (Yêu cầu `Idempotency-Key`)
- Cập nhật `new_slot_id`, `patient_name`, `patient_phone`, `reason`.

### 7.6. Hủy lịch khám
- **Endpoint**: `POST /bookings/{booking_id}/cancel` (Yêu cầu `Idempotency-Key`)
- Chuyển trạng thái sang `CANCELLED`, hoàn lại slot.

### 7.7. Lấy thông tin lịch khám bệnh & Deep Link
- **Endpoint**: `GET /bookings/{booking_id}` (Deep Link `/?booking_id={booking_id}`)
- **Endpoint**: `GET /bookings` (Tìm kiếm theo SĐT / Bệnh nhân / Bác sĩ)

## 8. Checklist trước khi submit

- [x] `operationId` duy nhất và ổn định.
- [x] Trạng thái khởi tạo `PENDING_PAYMENT` (Chưa thanh toán) và nút chuyển sang `PAID` (Thanh toán thành công).
- [x] Response mutation có `operation_id` chữ thường.
- [x] Hỗ trợ Deep Link `/?booking_id={booking_id}` xem trạng thái thanh toán và bấm thanh toán.
- [x] Hỗ trợ đủ 6 chức năng + luồng thanh toán.
- [x] OpenAPI validate pass.
