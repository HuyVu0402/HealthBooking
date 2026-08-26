# HealthBooking - Thông tin đăng ký Mini App

File này dùng để điền form Partner Registration cho mini-app HealthBooking.

URL production đã deploy:

```text
https://healthbooking.onrender.com
```

Không đưa `OUTBOUND_API_KEY`, Supabase key, token, password hoặc client secret vào Markdown, OpenAPI JSON hay mô tả công khai.

## 1. Thông tin cơ bản

| Trường trên form | Giá trị cần điền |
|---|---|
| Mã dịch vụ | `HEALTH_BOOKING` |
| Tên dịch vụ | `Health Booking` |
| Mô tả chi tiết | `Mini-app hỗ trợ người dùng tìm bác sĩ theo chuyên khoa, xem ca khám còn chỗ, đặt lịch khám, kiểm tra lịch đã đặt, đổi sang ca khác của cùng bác sĩ và hủy lịch. Đây là bản demo in-memory, không cung cấp chẩn đoán hoặc tư vấn y tế.` |
| Danh mục | `HEALTHCARE` hoặc `Y tế` |
| Base URL API | `https://healthbooking.onrender.com` |
| Health Check URL | `https://healthbooking.onrender.com/health` |
| Dịch vụ nhạy cảm | `Bật` |
| Outbound API Key | Để trống khi demo, hoặc tự tạo secret riêng và chỉ điền trong ô secret của dashboard |

Ghi chú: Guide khuyến nghị mã dịch vụ chữ thường, nhưng backend HealthBooking hiện trả `SERVICE_CODE=HEALTH_BOOKING`. Khi đăng ký bản này, nên giữ `HEALTH_BOOKING` để khớp backend và tài liệu mini-app hiện tại.

## 2. Cấu hình API

Chọn **Tải file OpenAPI JSON** và upload file:

```text
healthbooking-openapi.json
```

File này được sinh trực tiếp từ `main.py` bằng FastAPI OpenAPI schema.

Các endpoint trong spec:

| Method | Endpoint | Operation ID | Mục đích |
|---|---|---|---|
| `GET` | `/health` | `health_booking_status` | Kiểm tra mini-app hoạt động |
| `GET` | `/doctors` | `list_clinic_doctors` | Tìm bác sĩ theo chuyên khoa |
| `GET` | `/slots` | `search_clinic_slots` | Tìm ca khám còn chỗ |
| `POST` | `/bookings` | `create_clinic_booking` | Đặt lịch khám sau khi người dùng xác nhận |
| `GET` | `/bookings/{booking_id}` | `get_clinic_booking` | Xem thông tin lịch khám |
| `POST` | `/bookings/{booking_id}/cancel` | `cancel_clinic_booking` | Hủy lịch khám sau khi người dùng xác nhận |
| `POST` | `/bookings/{booking_id}/reschedule` | `reschedule_clinic_booking` | Đổi ca khám sau khi người dùng xác nhận |

Các endpoint mutation đã có metadata:

```json
{
  "x-risk-level": "high",
  "x-side-effect-type": "mutation",
  "x-requires-hitl": true,
  "x-idempotency-required": true,
  "x-retry-policy": "no_retry"
}
```

Các endpoint đọc dữ liệu có metadata:

```json
{
  "x-risk-level": "low",
  "x-side-effect-type": "read"
}
```

## 3. Cấu hình AI

| Trường trên form | Giá trị cần điền |
|---|---|
| Deep Link Template | `https://healthbooking.onrender.com/?booking_id={booking_id}` |
| Sample Intents | Xem danh sách bên dưới |
| Required Scopes | Để trống hoặc `end_user` |

Sample intents đề xuất:

```text
tìm bác sĩ nội tổng quát
tôi muốn đặt lịch khám nhi khoa
có ca khám mắt nào còn chỗ không
tìm ca khám với bác sĩ Nguyễn Minh Anh
đặt lịch khám sáng mai
kiểm tra lịch khám của tôi
đổi lịch khám sang ca khác
hủy lịch khám đã đặt
tôi muốn khám tai mũi họng
```

## 4. Kiểm tra trước khi gửi duyệt

- [x] `SERVICE_CODE=HEALTH_BOOKING`.
- [x] OpenAPI JSON có `openapi`, `info`, `servers`, `paths`.
- [x] Mỗi operation có `operationId` riêng.
- [x] Mutation có `Idempotency-Key` và HITL metadata.
- [x] Không đưa secret vào JSON hoặc Markdown.
- [x] Có ít nhất 4 bác sĩ mẫu.
- [x] Có luồng đặt, xem, đổi và hủy lịch.
- [x] Base URL public truy cập được.
- [ ] Nếu đặt `Outbound API Key`, cấu hình cùng giá trị đó trong biến môi trường `OUTBOUND_API_KEY`.
- [ ] Sau khi đăng ký, admin cần approve/publish service trong Catalog.

## 5. Lệnh kiểm tra nhanh

Git Bash:

```bash
curl "https://healthbooking.onrender.com/health"
curl "https://healthbooking.onrender.com/doctors"
curl "https://healthbooking.onrender.com/slots?doctor_id=DOC-NOI-01&available_only=true"
curl "https://healthbooking.onrender.com/openapi.json"
```

PowerShell:

```powershell
curl.exe https://healthbooking.onrender.com/health
curl.exe https://healthbooking.onrender.com/doctors
curl.exe "https://healthbooking.onrender.com/slots?doctor_id=DOC-NOI-01&available_only=true"
curl.exe https://healthbooking.onrender.com/openapi.json
```

## 6. Ghi chú Render

Nếu deploy lên Render, cấu hình:

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

Nếu đổi sang domain khác sau này, cập nhật:

- `PUBLIC_BASE_URL`
- `servers[0].url` trong `healthbooking-openapi.json`
- `Base URL API`
- `Health Check URL`
- `Deep Link Template`
