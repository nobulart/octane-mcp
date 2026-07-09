// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "octanex-canvas",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "octanex-canvas",
            path: "Sources/octanex-canvas",
            linkerSettings: [
                .unsafeFlags(["-framework", "WebKit"]),
                .unsafeFlags(["-framework", "AppKit"]),
            ]
        )
    ]
)
