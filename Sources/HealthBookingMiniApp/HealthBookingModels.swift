import Foundation

/// Data models matching this repo's own API contract (see main.py) — kept
/// internal to the package since the only public surface a host app needs is
/// `HealthBookingMiniAppView`.

struct HBEnvelope<T: Decodable>: Decodable {
    let status: String
    let message: String
    let data: T?
}

struct HBDoctorsData: Decodable {
    let doctors: [HBDoctor]
    let count: Int
}

struct HBSlotsData: Decodable {
    let slots: [HBSlot]
    let count: Int
}

struct HBDoctor: Identifiable, Decodable, Hashable {
    let doctorId: String
    let name: String
    let specialty: String
    let room: String
    let fee: Double
    let description: String

    var id: String { doctorId }

    enum CodingKeys: String, CodingKey {
        case doctorId = "doctor_id", name, specialty, room, fee, description
    }

    var feeFormatted: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.groupingSeparator = "."
        let amountText = formatter.string(from: NSNumber(value: fee)) ?? String(Int(fee))
        return "\(amountText)đ"
    }
}

struct HBSlot: Identifiable, Decodable, Hashable {
    let slotId: String
    let doctorId: String
    let date: String
    let startTime: String
    let endTime: String
    let remaining: Int
    let available: Bool

    var id: String { slotId }

    enum CodingKeys: String, CodingKey {
        case slotId = "slot_id", doctorId = "doctor_id", date
        case startTime = "start_time", endTime = "end_time"
        case remaining, available
    }

    var timeRangeText: String { "\(startTime) - \(endTime)" }
}
