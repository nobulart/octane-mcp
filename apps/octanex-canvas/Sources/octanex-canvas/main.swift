import AppKit
import WebKit

/// Minimal native host for the OctaneX Agentic Canvas web bundle.
///
/// The window is a single `WKWebView` loading ``apps/octanex-canvas/web/index.html``.
/// The browser bundle talks to the local HTTP gateway (``octanex_mcp.gateway``),
/// which this app optionally launches as a child process. No UI is injected into
/// Octane X itself.
final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    private var gatewayProc: Process?
    private var webView: WKWebView!

    func applicationDidFinishLaunching(_ notification: Notification) {
        let webDir = Self.findWebDir()

        let config = WKWebViewConfiguration()
        webView = WKWebView(frame: .zero, configuration: config)
        webView.autoresizingMask = [.width, .height]

        let rect = NSRect(x: 0, y: 0, width: 1280, height: 800)
        window = NSWindow(
            contentRect: rect,
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "OctaneX Agentic Canvas"
        window.contentView = webView
        window.center()

        let indexURL = webDir.appendingPathComponent("index.html")
        webView.loadFileURL(indexURL, allowingReadAccessTo: webDir)

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        startGateway()
    }

    func applicationWillTerminate(_ notification: Notification) {
        gatewayProc?.terminate()
    }

    // MARK: - Gateway lifecycle

    /// Launch the local HTTP gateway so the web bundle has something to talk to.
    /// Honors ``OCTANEX_RENDER_HOST`` from the app's own environment (set by the
    /// launcher) so the Studio thin-client path works without manual steps.
    private func startGateway() {
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/bin/bash")
        proc.arguments = ["-lc", "exec /opt/homebrew/bin/uv run --project /Users/craig/octanex-mcp python -m octanex_mcp.gateway"]
        var env = ProcessInfo.processInfo.environment
        if let rh = env["OCTANEX_RENDER_HOST"] {
            env["OCTANEX_RENDER_HOST"] = rh
        }
        proc.environment = env
        proc.standardOutput = nil
        proc.standardError = nil
        do {
            try proc.run()
            gatewayProc = proc
        } catch {
            NSLog("octanex-canvas: failed to launch gateway: \(error)")
        }
    }

    // MARK: - Helpers

    /// Locate the web bundle by walking up from the executable, falling back to
    /// the canonical repo path. Override with ``OCTANEX_WEB_DIR``.
    static func findWebDir() -> URL {
        if let env = ProcessInfo.processInfo.environment["OCTANEX_WEB_DIR"],
           FileManager.default.fileExists(atPath: (env as NSString).expandingTildeInPath) {
            return URL(fileURLWithPath: (env as NSString).expandingTildeInPath)
        }
        var dir = Bundle.main.bundleURL
        for _ in 0..<8 {
            let candidate = dir.appendingPathComponent("apps/octanex-canvas/web")
            if FileManager.default.fileExists(atPath: candidate.path) { return candidate }
            let parent = dir.deletingLastPathComponent()
            if parent == dir { break }
            dir = parent
        }
        return URL(fileURLWithPath: "/Users/craig/octanex-mcp/apps/octanex-canvas/web")
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
