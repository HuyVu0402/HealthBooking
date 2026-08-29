import Foundation
import Combine

/// Talks to this service's own read-only endpoints (`/doctors`, `/slots`) —
/// both `x-risk-level: low` on this service's catalog registration, so a
/// host super app is expected to call them directly from the client.
///
/// Booking/cancel/reschedule are `x-risk-level: high` + `x-requires-hitl: true`
/// (this service registers `is_sensitive: true`) and need the partner API key
/// configured on the deployment — a host app should never hold that key, so
/// this client only *composes* the booking request text; the host is
/// responsible for routing it through its own agent/HITL confirmation flow.
@MainActor
final class HealthBookingClient: ObservableObject {
    static let baseURL = "https://healthbooking.onrender.com"

    @Published var doctors: [HBDoctor] = []
    @Published var slots: [HBSlot] = []
    @Published var selectedDoctor: HBDoctor?
    @Published var isLoadingDoctors: Bool = false
    @Published var isLoadingSlots: Bool = false
    @Published var errorMessage: String?

    private let session: URLSession = {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 15
        return URLSession(configuration: configuration)
    }()

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    func fetchDoctors(specialty: String? = nil) async {
        isLoadingDoctors = true
        errorMessage = nil
        defer { isLoadingDoctors = false }
        do {
            var components = URLComponents(string: "\(Self.baseURL)/doctors")!
            if let specialty, !specialty.isEmpty {
                components.queryItems = [URLQueryItem(name: "specialty", value: specialty)]
            }
            let payload: HBDoctorsData = try await fetchEnvelope(url: components.url!)
            doctors = payload.doctors
        } catch {
            errorMessage = "Không tải được danh sách bác sĩ. Vui lòng thử lại."
        }
    }

    func fetchSlots(doctorId: String) async {
        isLoadingSlots = true
        errorMessage = nil
        defer { isLoadingSlots = false }
        do {
            var components = URLComponents(string: "\(Self.baseURL)/slots")!
            components.queryItems = [
                URLQueryItem(name: "doctor_id", value: doctorId),
                URLQueryItem(name: "available_only", value: "true"),
            ]
            let payload: HBSlotsData = try await fetchEnvelope(url: components.url!)
            slots = payload.slots
        } catch {
            errorMessage = "Không tải được ca khám còn chỗ. Vui lòng thử lại."
        }
    }

    /// The host app should hand this text to its own agent/HITL confirmation
    /// flow rather than calling `/bookings` directly (see file header).
    func composeBookingRequestMessage(doctor: HBDoctor, slot: HBSlot, patientName: String, patientPhone: String, reason: String) -> String {
        "Đặt lịch khám với \(doctor.name) (\(doctor.specialty)) vào ngày \(slot.date) lúc \(slot.startTime)-\(slot.endTime). " +
        "Bệnh nhân: \(patientName), SĐT: \(patientPhone). Lý do khám: \(reason)."
    }

    private func fetchEnvelope<T: Decodable>(url: URL) async throws -> T {
        let (data, response) = try await session.data(from: url)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        let envelope = try decoder.decode(HBEnvelope<T>.self, from: data)
        guard envelope.status == "success", let payload = envelope.data else {
            throw URLError(.cannotParseResponse)
        }
        return payload
    }
}
