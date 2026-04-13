# starter-android

Starter template for Kotlin/Jetpack Compose Android applications.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

## What this is for

Native Android applications that provide mobile interfaces for backend services.
Connects to APIs (starter-api, starter-gateway), receives push notifications
(starter-notification via FCM), and presents data with offline-first UX.

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Native Android app | **starter-android** |
| Native iOS app | starter-ios |
| Cross-platform desktop app | starter-desktop |
| Web frontend (responsive/PWA) | starter-web |
| Mobile companion to a web SaaS | **starter-android** + starter-web |

## Compatible starters

- **starter-api** -- backend REST API consumed by the Android app
- **starter-gateway** -- API gateway/BFF for mobile-optimised endpoints
- **starter-notification** -- push notification delivery via FCM
- **starter-realtime** -- WebSocket connection for live updates
- **starter-audit** -- user actions forwarded as audit events via API
- **starter-observability** -- OTel traces from the Android SDK feed into the collector

## Key characteristics

- **Compose-first** -- modern declarative UI with XML escape hatches for legacy
- **Offline-first** -- Room database with WorkManager for background sync
- **Secure storage** -- EncryptedSharedPreferences for tokens, BiometricPrompt for sensitive actions
- **Push notifications** -- FCM integration with data and notification messages
- **Observability** -- OTel Android SDK for distributed traces
- **Accessibility** -- TalkBack, content descriptions, minimum touch targets

## Tech stack

Kotlin, Jetpack Compose, Kotlin Flow, Hilt, Room, OkHttp, Retrofit, JUnit 5,
Espresso, Robolectric

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
- Google Health Connect integration

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
