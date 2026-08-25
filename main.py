from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, Header, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


SERVICE_CODE = os.getenv("SERVICE_CODE", "HEALTH_BOOKING")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8502")
OUTBOUND_API_KEY = os.getenv("OUTBOUND_API_KEY", "")
SLOT_CAPACITY = 2

app = FastAPI(
    title="Health Booking Mini App",
    version="1.0.0",
    description="Mini-app demo đặt, đổi và hủy lịch khám; dữ liệu lưu tạm trong bộ nhớ.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Customer(BaseModel):
    full_name: str | None = Field(None, description="Tên khách hàng do Super App cung cấp")
    email: str | None = Field(None, description="Email khách hàng do Super App cung cấp")
    username: str | None = Field(None, description="Tên đăng nhập do Super App cung cấp")


class BookingRequest(BaseModel):
    doctor_id: str = Field(..., description="Mã bác sĩ được chọn")
    slot_id: str = Field(..., description="Mã ca khám còn chỗ được chọn")
    patient_name: str = Field(..., min_length=2, max_length=100, description="Họ tên người đi khám")
    patient_phone: str = Field(..., min_length=8, max_length=20, description="Số điện thoại liên hệ")
    reason: str = Field(..., min_length=3, max_length=300, description="Lý do hoặc triệu chứng cần khám")
    customer: Customer | None = Field(None, description="Hồ sơ người dùng do Super App tự đính kèm")


class CancelRequest(BaseModel):
    reason: str | None = Field(None, max_length=300, description="Lý do hủy lịch khám")
    customer: Customer | None = Field(None, description="Hồ sơ người dùng do Super App tự đính kèm")


class RescheduleRequest(BaseModel):
    new_slot_id: str = Field(..., description="Mã ca khám mới còn chỗ của cùng bác sĩ")
    customer: Customer | None = Field(None, description="Hồ sơ người dùng do Super App tự đính kèm")


DOCTORS: dict[str, dict[str, Any]] = {
    "DOC-NOI-01": {
        "doctor_id": "DOC-NOI-01",
        "name": "BS. Nguyễn Minh Anh",
        "specialty": "Nội tổng quát",
        "room": "P.201",
        "fee": 250_000,
        "description": "Khám sức khỏe tổng quát, ho, sốt và các triệu chứng thông thường.",
    },
    "DOC-NHI-01": {
        "doctor_id": "DOC-NHI-01",
        "name": "BS. Trần Thu Hà",
        "specialty": "Nhi khoa",
        "room": "P.202",
        "fee": 280_000,
        "description": "Khám bệnh cho trẻ em và tư vấn chăm sóc sức khỏe trẻ nhỏ.",
    },
    "DOC-MAT-01": {
        "doctor_id": "DOC-MAT-01",
        "name": "BS. Lê Quốc Bảo",
        "specialty": "Mắt",
        "room": "P.203",
        "fee": 300_000,
        "description": "Khám thị lực, đau mắt, khô mắt và tư vấn tật khúc xạ.",
    },
    "DOC-TMH-01": {
        "doctor_id": "DOC-TMH-01",
        "name": "BS. Phạm Ngọc Lan",
        "specialty": "Tai Mũi Họng",
        "room": "P.204",
        "fee": 280_000,
        "description": "Khám tai, mũi, họng và các triệu chứng đường hô hấp trên.",
    },
}

SLOTS: dict[str, dict[str, Any]] = {}
BOOKINGS: dict[str, dict[str, Any]] = {}
IDEMPOTENCY_RESULTS: dict[str, dict[str, Any]] = {}


def envelope(status: Literal["success", "error"], message: str, data: Any = None, code: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"status": status, "message": message}
    if data is not None:
        result["data"] = data
    if code:
        result["code"] = code
    return result


def ok(data: Any, message: str) -> dict[str, Any]:
    return envelope("success", message, data)


def error(message: str, code: str, data: Any = None) -> dict[str, Any]:
    return envelope("error", message, data, code)


def verify_api_key(value: str | None) -> dict[str, Any] | None:
    if OUTBOUND_API_KEY and value != OUTBOUND_API_KEY:
        return error("API key không hợp lệ", "INVALID_API_KEY")
    return None


def require_idempotency(key: str | None) -> dict[str, Any] | None:
    if not key:
        return error("Thiếu Idempotency-Key", "IDEMPOTENCY_KEY_REQUIRED")
    return None


def seed_slots() -> None:
    """Tạo ca 30 phút cho 7 ngày tới; Chủ nhật phòng khám nghỉ."""
    if SLOTS:
        return
    start = date.today() + timedelta(days=1)
    session_times = (time(8, 0), time(8, 30), time(9, 0), time(9, 30), time(14, 0), time(14, 30), time(15, 0))
    for offset in range(7):
        day = start + timedelta(days=offset)
        if day.weekday() == 6:
            continue
        for doctor_id in DOCTORS:
            for at in session_times:
                slot_id = f"{doctor_id}-{day:%Y%m%d}-{at:%H%M}"
                SLOTS[slot_id] = {
                    "slot_id": slot_id,
                    "doctor_id": doctor_id,
                    "date": day.isoformat(),
                    "start_time": at.strftime("%H:%M"),
                    "end_time": (datetime.combine(day, at) + timedelta(minutes=30)).strftime("%H:%M"),
                    "capacity": SLOT_CAPACITY,
                    "booked": 0,
                }


def public_slot(slot: dict[str, Any]) -> dict[str, Any]:
    remaining = slot["capacity"] - slot["booked"]
    return {**slot, "remaining": remaining, "available": remaining > 0}


def booking_view(booking: dict[str, Any]) -> dict[str, Any]:
    doctor = DOCTORS[booking["doctor_id"]]
    slot = SLOTS[booking["slot_id"]]
    return {
        **booking,
        "doctor_name": doctor["name"],
        "specialty": doctor["specialty"],
        "room": doctor["room"],
        "fee": doctor["fee"],
        "date": slot["date"],
        "start_time": slot["start_time"],
        "end_time": slot["end_time"],
    }


seed_slots()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home() -> str:
    return r'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Health Booking</title><style>
:root{font-family:Inter,Arial,sans-serif;color:#183153;background:#f3f7fb}*{box-sizing:border-box}body{margin:0}
header{background:linear-gradient(120deg,#087f8c,#05a081);color:white;padding:28px 20px}header div,main{max-width:1050px;margin:auto}
h1{margin:0 0 6px}.muted{color:#63768d}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
main{padding:22px;display:grid;gap:18px}.panel,.card{background:white;border:1px solid #dce6ef;border-radius:12px;padding:16px;box-shadow:0 4px 16px #24405b0d}
.card h3{margin:0 0 6px}.tag{display:inline-block;background:#e6f7f2;color:#08765f;border-radius:20px;padding:4px 9px;font-size:12px;font-weight:700}
form{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;align-items:end}label{display:grid;gap:6px;font-size:13px;font-weight:700}
input,select,textarea,button{font:inherit;border:1px solid #bdcad6;border-radius:8px;padding:10px}textarea{min-height:42px}button{background:#078674;color:white;border:0;font-weight:700;cursor:pointer}.danger{background:#c23b3b}.secondary{background:#47637d}
.actions{display:flex;gap:8px;flex-wrap:wrap}.result{white-space:pre-wrap;background:#12263a;color:#eaf7f5;padding:14px;border-radius:9px;overflow:auto}
</style></head><body><header><div><h1>Health Booking</h1><span>Mini-app demo đặt lịch khám nhanh</span></div></header><main>
<section><h2>Bác sĩ</h2><div id="doctors" class="grid"></div></section>
<section class="panel"><h2>Đặt lịch</h2><form id="bookForm">
<label>Bác sĩ<select name="doctor_id" id="doctorSelect" required></select></label>
<label>Ca còn trống<select name="slot_id" id="slotSelect" required></select></label>
<label>Họ tên<input name="patient_name" value="Nguyễn Văn A" required></label>
<label>Điện thoại<input name="patient_phone" value="0912345678" required></label>
<label>Lý do khám<textarea name="reason" required>Khám sức khỏe tổng quát</textarea></label>
<button type="submit">Đặt lịch</button></form></section>
<section class="panel"><h2>Lịch vừa thao tác</h2><div id="bookingBox" class="muted">Chưa có lịch khám.</div></section>
<section><h2>Kết quả API</h2><pre id="result" class="result">Sẵn sàng.</pre></section>
</main><script>
const state={booking:null};const result=document.querySelector('#result');const doctorSelect=document.querySelector('#doctorSelect');const slotSelect=document.querySelector('#slotSelect');
async function api(url,options){const res=await fetch(url,options);const body=await res.json();result.textContent=JSON.stringify(body,null,2);return body}
async function loadDoctors(){const body=await api('/doctors');const ds=body.data.doctors;doctorSelect.innerHTML=ds.map(d=>`<option value="${d.doctor_id}">${d.name} — ${d.specialty}</option>`).join('');document.querySelector('#doctors').innerHTML=ds.map(d=>`<article class="card"><span class="tag">${d.specialty}</span><h3>${d.name}</h3><p>${d.description}</p><p class="muted">${d.room} · ${d.fee.toLocaleString('vi-VN')}đ</p></article>`).join('');await loadSlots()}
async function loadSlots(){const body=await api(`/slots?doctor_id=${encodeURIComponent(doctorSelect.value)}&available_only=true`);slotSelect.innerHTML=body.data.slots.map(s=>`<option value="${s.slot_id}">${s.date} · ${s.start_time}–${s.end_time} · còn ${s.remaining}</option>`).join('')||'<option value="">Không còn ca trống</option>'}
function renderBooking(){if(!state.booking){document.querySelector('#bookingBox').innerHTML='Chưa có lịch khám.';return}const b=state.booking;document.querySelector('#bookingBox').innerHTML=`<div class="card"><h3>${b.doctor_name}</h3><p>${b.specialty} · ${b.date} · ${b.start_time}–${b.end_time}</p><p><b>${b.patient_name}</b> — ${b.status}</p><div class="actions"><button class="secondary" onclick="reschedule()">Đổi sang ca đang chọn</button><button class="danger" onclick="cancelBooking()">Hủy lịch</button></div></div>`}
document.querySelector('#bookForm').addEventListener('submit',async e=>{e.preventDefault();const payload=Object.fromEntries(new FormData(e.target).entries());const body=await api('/bookings',{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()},body:JSON.stringify(payload)});if(body.status==='success'){state.booking=body.data.booking;renderBooking();await loadSlots()}})
async function cancelBooking(){if(!state.booking||!confirm('Bạn muốn hủy lịch này?'))return;const body=await api(`/bookings/${state.booking.booking_id}/cancel`,{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({reason:'Người dùng hủy trên giao diện demo'})});if(body.status==='success'){state.booking=body.data.booking;renderBooking();await loadSlots()}}
async function reschedule(){if(!state.booking||!slotSelect.value)return;const body=await api(`/bookings/${state.booking.booking_id}/reschedule`,{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({new_slot_id:slotSelect.value})});if(body.status==='success'){state.booking=body.data.booking;renderBooking();await loadSlots()}}
doctorSelect.addEventListener('change',loadSlots);loadDoctors();
</script></body></html>'''


@app.get("/health", operation_id="health_booking_status", summary="Kiểm tra Health Booking", openapi_extra={"x-risk-level": "low", "x-side-effect-type": "read"})
async def health() -> dict[str, Any]:
    return ok({"service_code": SERVICE_CODE, "storage": "memory", "status": "ok", "time": datetime.now(timezone.utc).isoformat()}, "Health Booking đang hoạt động")


@app.get("/doctors", operation_id="list_clinic_doctors", summary="Tìm bác sĩ theo chuyên khoa", description="Dùng khi người dùng muốn xem hoặc tìm bác sĩ phù hợp.", openapi_extra={"x-risk-level": "low", "x-side-effect-type": "read"})
async def list_doctors(specialty: str | None = Query(None, description="Chuyên khoa cần tìm, ví dụ: Nội tổng quát, Nhi khoa, Mắt, Tai Mũi Họng")) -> dict[str, Any]:
    doctors = [doctor for doctor in DOCTORS.values() if not specialty or specialty.lower() in doctor["specialty"].lower()]
    return ok({"doctors": doctors, "count": len(doctors)}, "Lấy danh sách bác sĩ thành công")


@app.get("/slots", operation_id="search_clinic_slots", summary="Tìm ca khám còn chỗ", description="Dùng khi người dùng đã chọn bác sĩ hoặc ngày khám và muốn xem ca còn trống.", openapi_extra={"x-risk-level": "low", "x-side-effect-type": "read"})
async def list_slots(
    doctor_id: str | None = Query(None, description="Mã bác sĩ cần xem lịch"),
    appointment_date: date | None = Query(None, description="Ngày muốn khám theo định dạng YYYY-MM-DD"),
    available_only: bool = Query(True, description="Chỉ trả về ca còn chỗ"),
) -> dict[str, Any]:
    if doctor_id and doctor_id not in DOCTORS:
        return error("Không tìm thấy bác sĩ", "DOCTOR_NOT_FOUND", {"doctor_id": doctor_id})
    slots = []
    for slot in SLOTS.values():
        item = public_slot(slot)
        if doctor_id and slot["doctor_id"] != doctor_id:
            continue
        if appointment_date and slot["date"] != appointment_date.isoformat():
            continue
        if available_only and not item["available"]:
            continue
        slots.append(item)
    slots.sort(key=lambda item: (item["date"], item["start_time"], item["doctor_id"]))
    return ok({"slots": slots, "count": len(slots)}, "Lấy danh sách ca khám thành công")


@app.post("/bookings", operation_id="create_clinic_booking", summary="Đặt lịch khám sau khi người dùng xác nhận", description="Dùng khi người dùng đã chọn bác sĩ, ca khám và cung cấp thông tin bệnh nhân.", openapi_extra={"x-risk-level": "high", "x-side-effect-type": "mutation", "x-requires-hitl": True, "x-idempotency-required": True, "x-retry-policy": "no_retry", "x-deep-link-template": f"{PUBLIC_BASE_URL}/?booking_id={{booking_id}}"})
async def create_booking(payload: BookingRequest, idempotency_key: str | None = Header(None, alias="Idempotency-Key"), x_api_key: str | None = Header(None, alias="x-api-key")) -> dict[str, Any]:
    if key_error := verify_api_key(x_api_key):
        return key_error
    if idem_error := require_idempotency(idempotency_key):
        return idem_error
    if idempotency_key in IDEMPOTENCY_RESULTS:
        return IDEMPOTENCY_RESULTS[idempotency_key]
    doctor = DOCTORS.get(payload.doctor_id)
    slot = SLOTS.get(payload.slot_id)
    if not doctor:
        return error("Không tìm thấy bác sĩ", "DOCTOR_NOT_FOUND")
    if not slot or slot["doctor_id"] != payload.doctor_id:
        return error("Ca khám không thuộc bác sĩ đã chọn", "INVALID_SLOT")
    if slot["booked"] >= slot["capacity"]:
        return error("Ca khám đã hết chỗ", "SLOT_FULL", public_slot(slot))
    booking_id = f"CLB-{uuid4().hex[:8].upper()}"
    booking = {
        "booking_id": booking_id,
        "doctor_id": payload.doctor_id,
        "slot_id": payload.slot_id,
        "patient_name": payload.patient_name,
        "patient_phone": payload.patient_phone,
        "reason": payload.reason,
        "status": "CONFIRMED",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    BOOKINGS[booking_id] = booking
    slot["booked"] += 1
    response = ok({"booking": booking_view(booking)}, "Đặt lịch khám thành công")
    IDEMPOTENCY_RESULTS[idempotency_key] = response
    return response


@app.get("/bookings/{booking_id}", operation_id="get_clinic_booking", summary="Xem thông tin lịch khám", description="Dùng khi người dùng muốn kiểm tra lịch khám đã đặt.", openapi_extra={"x-risk-level": "low", "x-side-effect-type": "read"})
async def get_booking(booking_id: str = Path(..., description="Mã lịch khám cần xem")) -> dict[str, Any]:
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return error("Không tìm thấy lịch khám", "BOOKING_NOT_FOUND")
    return ok({"booking": booking_view(booking)}, "Lấy lịch khám thành công")


@app.post("/bookings/{booking_id}/cancel", operation_id="cancel_clinic_booking", summary="Hủy lịch khám sau khi người dùng xác nhận", description="Dùng khi người dùng muốn hủy lịch khám đã đặt.", openapi_extra={"x-risk-level": "high", "x-side-effect-type": "mutation", "x-requires-hitl": True, "x-idempotency-required": True, "x-retry-policy": "no_retry"})
async def cancel_booking(payload: CancelRequest, booking_id: str = Path(..., description="Mã lịch khám cần hủy"), idempotency_key: str | None = Header(None, alias="Idempotency-Key"), x_api_key: str | None = Header(None, alias="x-api-key")) -> dict[str, Any]:
    if key_error := verify_api_key(x_api_key):
        return key_error
    if idem_error := require_idempotency(idempotency_key):
        return idem_error
    cache_key = f"cancel:{idempotency_key}"
    if cache_key in IDEMPOTENCY_RESULTS:
        return IDEMPOTENCY_RESULTS[cache_key]
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return error("Không tìm thấy lịch khám", "BOOKING_NOT_FOUND")
    if booking["status"] != "CANCELLED":
        SLOTS[booking["slot_id"]]["booked"] -= 1
        booking.update(status="CANCELLED", cancel_reason=payload.reason, cancelled_at=datetime.now(timezone.utc).isoformat())
    response = ok({"booking": booking_view(booking)}, "Hủy lịch khám thành công")
    IDEMPOTENCY_RESULTS[cache_key] = response
    return response


@app.post("/bookings/{booking_id}/reschedule", operation_id="reschedule_clinic_booking", summary="Đổi ca khám sau khi người dùng xác nhận", description="Dùng khi người dùng muốn chuyển lịch hiện tại sang một ca khác của cùng bác sĩ.", openapi_extra={"x-risk-level": "high", "x-side-effect-type": "mutation", "x-requires-hitl": True, "x-idempotency-required": True, "x-retry-policy": "no_retry"})
async def reschedule_booking(payload: RescheduleRequest, booking_id: str = Path(..., description="Mã lịch khám cần đổi"), idempotency_key: str | None = Header(None, alias="Idempotency-Key"), x_api_key: str | None = Header(None, alias="x-api-key")) -> dict[str, Any]:
    if key_error := verify_api_key(x_api_key):
        return key_error
    if idem_error := require_idempotency(idempotency_key):
        return idem_error
    cache_key = f"reschedule:{idempotency_key}"
    if cache_key in IDEMPOTENCY_RESULTS:
        return IDEMPOTENCY_RESULTS[cache_key]
    booking = BOOKINGS.get(booking_id)
    new_slot = SLOTS.get(payload.new_slot_id)
    if not booking:
        return error("Không tìm thấy lịch khám", "BOOKING_NOT_FOUND")
    if booking["status"] == "CANCELLED":
        return error("Không thể đổi một lịch đã hủy", "BOOKING_CANCELLED")
    if not new_slot or new_slot["doctor_id"] != booking["doctor_id"]:
        return error("Ca mới phải thuộc cùng bác sĩ", "INVALID_NEW_SLOT")
    if new_slot["booked"] >= new_slot["capacity"]:
        return error("Ca khám mới đã hết chỗ", "SLOT_FULL", public_slot(new_slot))
    if payload.new_slot_id != booking["slot_id"]:
        SLOTS[booking["slot_id"]]["booked"] -= 1
        new_slot["booked"] += 1
        booking.update(slot_id=payload.new_slot_id, rescheduled_at=datetime.now(timezone.utc).isoformat())
    response = ok({"booking": booking_view(booking)}, "Đổi ca khám thành công")
    IDEMPOTENCY_RESULTS[cache_key] = response
    return response
