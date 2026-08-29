// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "HealthBookingMiniApp",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "HealthBookingMiniApp", targets: ["HealthBookingMiniApp"]),
    ],
    targets: [
        .target(name: "HealthBookingMiniApp"),
    ]
)
