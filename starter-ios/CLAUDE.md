# CLAUDE.md -- {PROJECT_NAME}-ios

This file covers coding conventions for this iOS application. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

---

## Stack

- **Swift 5.9+**, minimum deployment target iOS 17
- **UI:** SwiftUI (UIKit only for legacy/unsupported components)
- **Architecture:** MVVM with Combine and async/await
- **Networking:** URLSession with async/await, retry with exponential backoff, certificate pinning
- **Auth:** Keychain for token storage, biometric auth (Face ID / Touch ID)
- **Logging:** os_log with structured categories
- **Observability:** OpenTelemetry Swift SDK for distributed traces
- **Testing:** XCTest for unit tests, XCUITest for UI tests
- **CI:** GitHub Actions + Xcode Cloud, TestFlight for beta distribution
- **Package management:** Swift Package Manager (no CocoaPods)

---

## Project structure (planned)

```
{ProjectName}/
├── App/
│   ├── {ProjectName}App.swift     # @main entry point, scene configuration
│   ├── AppDelegate.swift          # Push notification registration, lifecycle
│   └── ContentView.swift          # Root navigation view
├── Features/
│   └── {Feature}/
│       ├── Views/                 # SwiftUI views
│       ├── ViewModels/            # ObservableObject view models
│       └── Models/                # Feature-specific data models
├── Core/
│   ├── Networking/
│   │   ├── APIClient.swift        # URLSession wrapper with auth, retry, pinning
│   │   ├── Endpoints.swift        # Typed endpoint definitions
│   │   └── TokenManager.swift     # Keychain-backed token refresh
│   ├── Persistence/
│   │   ├── DataController.swift   # Core Data / SwiftData stack
│   │   └── SyncQueue.swift        # Offline operation queue
│   ├── Auth/
│   │   ├── KeychainHelper.swift   # Keychain read/write/delete
│   │   └── BiometricAuth.swift    # Face ID / Touch ID wrapper
│   ├── Logging/
│   │   └── Logger.swift           # os_log categories and convenience methods
│   └── Observability/
│       └── OTelSetup.swift        # OpenTelemetry SDK initialisation
├── Resources/
│   ├── Assets.xcassets            # App icons, colours, images
│   ├── Localizable.xcstrings      # Localised strings
│   └── Info.plist
└── Tests/
    ├── UnitTests/                 # XCTest unit tests
    └── UITests/                   # XCUITest UI tests
```

---

## Conventions

### General
- Swift strict concurrency mode enabled
- All public APIs must have documentation comments (///)
- No force unwrapping (!) except in tests and @IBOutlet (if UIKit is used)
- No `print()` in production code -- use os_log via the Logger utility
- Never hardcode secrets, API keys, or URLs -- read from configuration or environment
- Never commit signing certificates or provisioning profiles

### SwiftUI
- Views should be small and composable -- extract subviews at ~50 lines
- Use `@Observable` (iOS 17+) or `@ObservableObject` for view models
- Prefer `@Environment` for dependency injection over singletons
- Use `@ViewBuilder` for conditional view composition
- Support Dynamic Type and VoiceOver accessibility on all interactive elements

### Networking
- All network requests go through `APIClient` -- never use URLSession directly
- Use async/await for all network calls
- Implement retry with exponential backoff for transient failures (5xx, timeout)
- Certificate pinning for production API endpoints
- Handle offline gracefully -- queue operations for later sync

### Authentication
- Store tokens in Keychain, never in UserDefaults or plain files
- Use BiometricPrompt for sensitive operations (payments, settings changes)
- Implement token refresh transparently in APIClient
- Clear Keychain on logout

### Persistence
- Use Core Data or SwiftData for structured local data
- Design for offline-first: read from local store, sync with server
- SyncQueue: failed network writes are queued and retried when connectivity returns
- Never block the main thread with database operations

### Logging
- Use os_log with subsystem = Bundle.identifier, category per feature
- Log levels: `.debug` for development, `.info` for business events,
  `.error` for failures, `.fault` for critical issues
- Include correlation IDs from API responses in log entries
- Never log sensitive data (tokens, passwords, PII)

### Observability
- Initialise OTel SDK early in app launch (AppDelegate or @main)
- Create spans for network requests, database operations, and key user flows
- Propagate trace context in HTTP headers to backend services
- Add span attributes: `user.id`, `feature.name`, `api.endpoint`

### Security
- App Transport Security (ATS) enforced -- no HTTP exceptions
- Data at rest encryption via Data Protection API (NSFileProtectionComplete)
- No secrets in code, xcconfig, or Info.plist -- use runtime configuration
- Implement jailbreak detection for sensitive financial/healthcare apps
- Use `SecureField` for password inputs

### Testing
- Every ViewModel needs unit tests for state transitions and error handling
- Mock network layer using protocol-based dependency injection
- XCUITest for critical user flows (login, main feature, error states)
- Tests must not depend on each other or on execution order
- Use test fixtures for consistent mock data

---

## Common commands (planned)

```bash
# Build
xcodebuild -scheme {ProjectName} -destination 'platform=iOS Simulator,name=iPhone 15'

# Test
xcodebuild test -scheme {ProjectName} -destination 'platform=iOS Simulator,name=iPhone 15'

# Lint (SwiftLint)
swiftlint lint --strict

# Format (swift-format)
swift-format format --recursive Sources/
```

---

## CI/CD approach

- **GitHub Actions** for PR checks (build, test, lint)
- **Xcode Cloud** for TestFlight builds on merge to main
- **TestFlight** for internal and beta distribution
- **App Store Connect API** for automated release submission
- Separate schemes for Debug, Staging, and Release configurations

---

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
swiftlint lint --strict && xcodebuild test -scheme {ProjectName} -destination 'platform=iOS Simulator,name=iPhone 15'
```
