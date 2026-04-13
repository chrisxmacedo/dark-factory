# CLAUDE.md -- {PROJECT_NAME}-android

This file covers coding conventions for this Android application. For
project-wide architecture, service providers, and secrets, see `../CLAUDE.md`
and `../.secrets.md` in the parent project directory.

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

---

## Stack

- **Kotlin**, minimum SDK 26 (Android 8), target SDK 35
- **UI:** Jetpack Compose (XML layouts only for legacy/unsupported components)
- **Architecture:** MVVM with Kotlin Flow and StateFlow
- **DI:** Hilt (Dagger under the hood)
- **Networking:** OkHttp + Retrofit with coroutine adapters, retry with exponential backoff, certificate pinning
- **Auth:** EncryptedSharedPreferences for token storage, BiometricPrompt for sensitive actions
- **Logging:** Timber with custom tree for production (no-op debug logs in release)
- **Observability:** OpenTelemetry Android SDK for distributed traces
- **Testing:** JUnit 5 for unit tests, Espresso for UI tests, Robolectric for fast Android tests
- **CI:** GitHub Actions + Gradle, Firebase App Distribution for beta builds
- **Package management:** Gradle version catalogs (libs.versions.toml)

---

## Project structure (planned)

```
app/
├── src/
│   ├── main/
│   │   ├── java/com/{org}/{project}/
│   │   │   ├── App.kt                      # Application class, Hilt entry point
│   │   │   ├── MainActivity.kt             # Single-activity host
│   │   │   ├── di/
│   │   │   │   ├── AppModule.kt            # Hilt app-scoped bindings
│   │   │   │   └── NetworkModule.kt        # OkHttp, Retrofit providers
│   │   │   ├── features/
│   │   │   │   └── {feature}/
│   │   │   │       ├── ui/                 # Composable screens and components
│   │   │   │       ├── viewmodel/          # ViewModel with StateFlow
│   │   │   │       └── model/              # Feature-specific data models
│   │   │   ├── core/
│   │   │   │   ├── network/
│   │   │   │   │   ├── ApiClient.kt        # Retrofit service factory
│   │   │   │   │   ├── AuthInterceptor.kt  # Token injection interceptor
│   │   │   │   │   └── RetryInterceptor.kt # Exponential backoff retry
│   │   │   │   ├── persistence/
│   │   │   │   │   ├── AppDatabase.kt      # Room database definition
│   │   │   │   │   └── SyncWorker.kt       # WorkManager background sync
│   │   │   │   ├── auth/
│   │   │   │   │   ├── TokenStore.kt       # EncryptedSharedPreferences wrapper
│   │   │   │   │   └── BiometricHelper.kt  # BiometricPrompt wrapper
│   │   │   │   ├── logging/
│   │   │   │   │   └── TimberSetup.kt      # Timber tree configuration
│   │   │   │   └── observability/
│   │   │   │       └── OTelSetup.kt        # OpenTelemetry SDK initialisation
│   │   │   └── navigation/
│   │   │       └── NavGraph.kt             # Compose Navigation graph
│   │   ├── res/                            # Resources, themes, strings
│   │   └── AndroidManifest.xml
│   ├── test/                               # JUnit 5 + Robolectric unit tests
│   └── androidTest/                        # Espresso UI tests
├── build.gradle.kts
└── gradle/
    └── libs.versions.toml                  # Version catalog
```

---

## Conventions

### General
- Kotlin coding conventions (ktlint enforced)
- All public APIs must have KDoc comments
- No `!!` (non-null assertion) except in tests -- use safe calls or require()
- No `Log.d()` / `println()` in production code -- use Timber
- Never hardcode secrets, API keys, or URLs -- read from BuildConfig or remote config
- Never commit signing keystores or google-services.json

### Jetpack Compose
- Composables should be small and composable -- extract at ~50 lines
- Use `collectAsStateWithLifecycle()` for StateFlow observation
- Prefer `CompositionLocal` for scoped dependency injection
- Use `@Preview` annotations for all reusable components
- Support TalkBack content descriptions and minimum 48dp touch targets

### Networking
- All network requests go through Retrofit services -- never use OkHttp directly
- Use suspend functions for all network calls
- Implement retry with exponential backoff via OkHttp interceptor (5xx, timeout)
- Certificate pinning for production API endpoints
- Handle offline gracefully -- queue operations via WorkManager

### Authentication
- Store tokens in EncryptedSharedPreferences, never in plain SharedPreferences
- Use BiometricPrompt for sensitive operations (payments, settings changes)
- Implement token refresh transparently in AuthInterceptor
- Clear all secure storage on logout

### Persistence
- Use Room for structured local data with type-safe DAOs
- Design for offline-first: read from Room, sync with server via WorkManager
- SyncWorker: failed network writes are queued and retried with backoff constraints
- Never block the main thread with database operations -- use Dispatchers.IO

### Logging
- Use Timber with a release tree that strips debug/verbose logs
- Log levels: `.d()` for development, `.i()` for business events,
  `.e()` for failures, `.wtf()` for critical issues
- Include correlation IDs from API responses in log entries
- Never log sensitive data (tokens, passwords, PII)

### Observability
- Initialise OTel SDK in Application.onCreate()
- Create spans for network requests, database operations, and key user flows
- Propagate trace context in HTTP headers to backend services
- Add span attributes: `user.id`, `feature.name`, `api.endpoint`

### Security
- Network security config enforcing HTTPS -- no cleartext traffic
- EncryptedSharedPreferences for all sensitive data at rest
- No secrets in code, BuildConfig, or res/values -- use runtime configuration
- Implement root/emulator detection for sensitive financial/healthcare apps
- ProGuard/R8 obfuscation enabled for release builds

### Testing
- Every ViewModel needs unit tests for state transitions and error handling
- Mock network layer using Hilt test modules with fake implementations
- Espresso for critical user flows (login, main feature, error states)
- Tests must not depend on each other or on execution order
- Use test fixtures and fake data factories for consistent mock data

---

## Common commands (planned)

```bash
# Build debug APK
./gradlew assembleDebug

# Run unit tests
./gradlew testDebugUnitTest

# Run instrumented tests (requires emulator or device)
./gradlew connectedDebugAndroidTest

# Lint
./gradlew ktlintCheck

# Format
./gradlew ktlintFormat
```

---

## CI/CD approach

- **GitHub Actions** for PR checks (build, test, lint, detekt)
- **Gradle** build with build cache and configuration cache enabled
- **Firebase App Distribution** for internal and beta builds on merge to ci
- **Google Play Console API** for automated release track uploads
- Separate build variants for Debug, Staging, and Release configurations

---

## Before opening a PR

Run all of these and fix any failures before pushing:

```bash
./gradlew ktlintCheck detekt testDebugUnitTest
```
