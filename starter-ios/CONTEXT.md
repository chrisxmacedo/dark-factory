# starter-ios

Starter template for Swift/SwiftUI iOS applications.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

## What this is for

Native iOS applications that provide mobile interfaces for backend services.
Connects to APIs (starter-api, starter-gateway), receives push notifications
(starter-notification via APNs), and presents data with offline-first UX.

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Native iOS app | **starter-ios** |
| Native Android app | starter-android |
| Cross-platform desktop app | starter-desktop |
| Web frontend (responsive/PWA) | starter-web |
| Mobile companion to a web SaaS | **starter-ios** + starter-web |

## Compatible starters

- **starter-api** -- backend REST API consumed by the iOS app
- **starter-gateway** -- API gateway/BFF for mobile-optimised endpoints
- **starter-notification** -- push notification delivery via APNs
- **starter-realtime** -- WebSocket connection for live updates
- **starter-audit** -- user actions forwarded as audit events via API
- **starter-observability** -- OTel traces from the iOS SDK feed into the collector

## Key characteristics

- **SwiftUI-first** -- modern declarative UI with UIKit escape hatches
- **Offline-first** -- local persistence with sync queue for network operations
- **Secure storage** -- Keychain for tokens, biometric auth for sensitive actions
- **Push notifications** -- APNs integration with rich notification support
- **Observability** -- OTel Swift SDK for distributed traces
- **Accessibility** -- VoiceOver, Dynamic Type, colour contrast compliance

## Tech stack

Swift 5.9+, SwiftUI, Combine, async/await, XCTest, XCUITest, Core Data / SwiftData

## Market applications

### Banking & Finance
- Mobile banking (account overview, transfers, card controls)
- P2P payments and payment requests
- Investment portfolio and market data
- Card freeze/unfreeze and spending alerts

### Healthcare
- Patient portal (records, lab results, care plan)
- Appointment booking and telehealth video
- Medication reminders and prescription management
- Health data sync via HealthKit

### E-commerce
- Shopping and product browsing
- Order tracking and delivery notifications
- Wishlist and saved items
- Barcode/QR scanning for in-store experience

### SaaS
- Mobile companion for web dashboard
- Notification centre and quick actions
- Team chat and collaboration features
- Offline data capture for field workers

### Insurance
- Claims filing with photo/document upload
- Policy management and digital ID cards
- Roadside assistance with location sharing
- Premium payment and billing history

### Legal
- Document review and annotation
- Case tracking and deadline alerts
- Secure messaging with attorneys
- Court date calendar integration
