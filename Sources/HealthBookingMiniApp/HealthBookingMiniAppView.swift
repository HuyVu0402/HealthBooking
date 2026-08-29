import SwiftUI

/// Drop-in mini-app UI for HealthBooking: browses real doctors/slots from
/// this service directly, then hands the finished booking request off to the
/// host app via `onBookingRequested` instead of calling `/bookings` itself.
///
/// The host is expected to route that text through its own agent/HITL
/// confirmation flow before actually booking — see HealthBookingClient's
/// header for why this mini-app never calls the mutation endpoints directly.
public struct HealthBookingMiniAppView: View {
    @StateObject private var client = HealthBookingClient()
    @Environment(\.dismiss) private var dismiss

    private let onBookingRequested: (String) -> Void

    private let hbTeal = Color(red: 0.03, green: 0.52, blue: 0.46)
    private let hbGreen = Color(red: 0.03, green: 0.63, blue: 0.55)

    @State private var specialtyFilter: String = ""
    @State private var selectedSlot: HBSlot?
    @State private var isBookingFormPresented: Bool = false

    /// - Parameter onBookingRequested: called with a composed natural-language
    ///   booking request once the patient confirms the form. The host app
    ///   should send this to its own agent/HITL flow, not call this
    ///   service's `/bookings` endpoint directly (it needs a secret key only
    ///   the host's backend should hold).
    public init(onBookingRequested: @escaping (String) -> Void) {
        self.onBookingRequested = onBookingRequested
    }

    public var body: some View {
        NavigationStack {
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 16) {
                    heroBanner
                    specialtyFilterBar
                    doctorsSection
                }
                .padding(.top, 8)
                .padding(.bottom, 32)
            }
            .navigationTitle("Health Booking")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button {
                        dismiss()
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "xmark.circle.fill")
                            Text("Đóng")
                        }
                        .foregroundColor(.secondary)
                    }
                }
            }
            .task {
                await client.fetchDoctors()
            }
            .sheet(item: $client.selectedDoctor, onDismiss: { selectedSlot = nil }) { doctor in
                slotPickerSheet(doctor: doctor)
            }
            .sheet(isPresented: $isBookingFormPresented) {
                if let doctor = client.selectedDoctor, let slot = selectedSlot {
                    bookingFormSheet(doctor: doctor, slot: slot)
                }
            }
        }
    }

    // MARK: - Hero Banner
    private var heroBanner: some View {
        ZStack(alignment: .bottomLeading) {
            RoundedRectangle(cornerRadius: 18)
                .fill(LinearGradient(colors: [hbTeal, hbGreen], startPoint: .topLeading, endPoint: .bottomTrailing))
                .frame(height: 120)

            VStack(alignment: .leading, spacing: 6) {
                Text("HEALTH BOOKING")
                    .font(.system(size: 9, weight: .heavy))
                    .foregroundColor(.yellow)
                Text("Đặt Lịch Khám Nhanh")
                    .font(.title3.bold())
                    .foregroundColor(.white)
                Text("Tìm bác sĩ theo chuyên khoa, xem ca còn trống và gửi yêu cầu đặt lịch")
                    .font(.caption2)
                    .foregroundColor(.white.opacity(0.9))
            }
            .padding(16)
        }
        .padding(.horizontal)
    }

    // MARK: - Specialty Filter
    private var specialtyFilterBar: some View {
        HStack(spacing: 10) {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            TextField("Lọc theo chuyên khoa (Nội tổng quát, Nhi khoa...)", text: $specialtyFilter)
                .font(.subheadline)
                .onSubmit {
                    Task { await client.fetchDoctors(specialty: specialtyFilter) }
                }
            if !specialtyFilter.isEmpty {
                Button {
                    specialtyFilter = ""
                    Task { await client.fetchDoctors() }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 9)
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .padding(.horizontal)
    }

    // MARK: - Doctors Section
    private var doctorsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Bác Sĩ Đang Nhận Khám (\(client.doctors.count))")
                    .font(.headline.bold())
                Spacer()
            }
            .padding(.horizontal)

            if client.isLoadingDoctors {
                ProgressView()
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 24)
            } else if let errorMessage = client.errorMessage {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.horizontal)
            } else {
                VStack(spacing: 12) {
                    ForEach(client.doctors) { doctor in
                        Button {
                            client.selectedDoctor = doctor
                            Task { await client.fetchSlots(doctorId: doctor.doctorId) }
                        } label: {
                            doctorCard(doctor: doctor)
                        }
                    }
                }
                .padding(.horizontal)
            }
        }
    }

    private func doctorCard(doctor: HBDoctor) -> some View {
        HStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(hbTeal.opacity(0.15))
                    .frame(width: 54, height: 54)
                Image(systemName: "person.crop.circle.fill")
                    .font(.system(size: 40))
                    .foregroundColor(hbTeal)
            }

            VStack(alignment: .leading, spacing: 3) {
                Text(doctor.name)
                    .font(.subheadline.bold())
                    .foregroundColor(.primary)
                Text(doctor.specialty)
                    .font(.caption.bold())
                    .foregroundColor(hbTeal)
                Text(doctor.description)
                    .font(.system(size: 10))
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 4) {
                Text(doctor.feeFormatted)
                    .font(.caption.bold())
                    .foregroundColor(.blue)
                Text("Xem ca khám")
                    .font(.caption2.bold())
                    .foregroundColor(.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(hbTeal)
                    .cornerRadius(6)
            }
        }
        .padding(12)
        .background(Color(.systemBackground))
        .cornerRadius(14)
        .shadow(color: .black.opacity(0.04), radius: 4, y: 2)
    }

    // MARK: - Slot Picker
    private func slotPickerSheet(doctor: HBDoctor) -> some View {
        NavigationStack {
            Group {
                if client.isLoadingSlots {
                    ProgressView()
                } else if client.slots.isEmpty {
                    ContentUnavailableView(
                        "Không còn ca trống",
                        systemImage: "calendar.badge.exclamationmark",
                        description: Text("Vui lòng chọn bác sĩ khác hoặc quay lại sau.")
                    )
                } else {
                    List(client.slots) { slot in
                        Button {
                            selectedSlot = slot
                            isBookingFormPresented = true
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(slot.date)
                                        .font(.subheadline.bold())
                                    Text(slot.timeRangeText)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                Spacer()
                                Text("Còn \(slot.remaining) chỗ")
                                    .font(.caption2.bold())
                                    .foregroundColor(hbTeal)
                            }
                        }
                    }
                }
            }
            .navigationTitle(doctor.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Đóng") { client.selectedDoctor = nil }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }

    // MARK: - Booking Form
    private func bookingFormSheet(doctor: HBDoctor, slot: HBSlot) -> some View {
        BookingRequestForm(doctor: doctor, slot: slot) { patientName, patientPhone, reason in
            let message = client.composeBookingRequestMessage(
                doctor: doctor, slot: slot, patientName: patientName, patientPhone: patientPhone, reason: reason
            )
            isBookingFormPresented = false
            client.selectedDoctor = nil
            onBookingRequested(message)
        }
    }
}

/// Patient details form; submitting hands the request to the host app rather
/// than calling this service's booking endpoint itself (see file header).
private struct BookingRequestForm: View {
    let doctor: HBDoctor
    let slot: HBSlot
    let onSubmit: (_ patientName: String, _ patientPhone: String, _ reason: String) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var patientName: String = ""
    @State private var patientPhone: String = ""
    @State private var reason: String = ""

    private var isValid: Bool {
        patientName.count >= 2 && patientPhone.count >= 8 && reason.count >= 3
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Lịch khám đã chọn") {
                    Text("\(doctor.name) • \(doctor.specialty)")
                    Text("\(slot.date), \(slot.timeRangeText)")
                        .foregroundColor(.secondary)
                }
                Section("Thông tin bệnh nhân") {
                    TextField("Họ và tên", text: $patientName)
                    TextField("Số điện thoại", text: $patientPhone)
                        .keyboardType(.phonePad)
                    TextField("Lý do khám", text: $reason, axis: .vertical)
                        .lineLimit(2...4)
                }
                Section {
                    Text("Yêu cầu sẽ được gửi tới hệ thống xác nhận của ứng dụng trước khi đặt lịch thật với HealthBooking.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .navigationTitle("Xác nhận thông tin")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Hủy") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Gửi yêu cầu") {
                        onSubmit(patientName, patientPhone, reason)
                    }
                    .disabled(!isValid)
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}
