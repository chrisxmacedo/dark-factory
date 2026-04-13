# starter-desktop

Starter template for cross-platform desktop applications (Tauri preferred, Electron fallback).

**Status: PLACEHOLDER -- conventions documented, code scaffold pending first project.**

## What this is for

Cross-platform desktop applications that run on macOS, Windows, and Linux.
Connects to APIs (starter-api, starter-gateway), receives real-time updates
(starter-realtime via WebSocket), and provides rich native-feeling UX with
system tray, keyboard shortcuts, and local file access.

## When to use this vs other starters

| Use case | Template |
|----------|----------|
| Cross-platform desktop app | **starter-desktop** |
| Native iOS app | starter-ios |
| Native Android app | starter-android |
| Web frontend (browser-only) | starter-web |
| Browser extension overlay | starter-chrome-extension |
| Desktop + mobile companion | **starter-desktop** + starter-ios / starter-android |

## Compatible starters

- **starter-api** -- backend REST API consumed by the desktop app
- **starter-gateway** -- API gateway/BFF for optimised endpoints
- **starter-realtime** -- WebSocket connection for live data streaming
- **starter-notification** -- desktop notifications via native OS APIs
- **starter-audit** -- user actions forwarded as audit events via API
- **starter-observability** -- OTel traces from the desktop app feed into the collector
- **starter-docs** -- document generation triggered from desktop workflows

## Key characteristics

- **Tauri preferred** -- Rust backend with web frontend, small binary, native performance
- **React/TypeScript frontend** -- shared component patterns with starter-web
- **Auto-update** -- built-in update mechanism with signature verification
- **Code signing** -- macOS notarisation, Windows Authenticode, Linux AppImage
- **System integration** -- tray icon, global shortcuts, file associations, deep links
- **Offline-capable** -- local SQLite for offline data, sync when connected

## Tech stack

Tauri 2.x, Rust (backend), React, TypeScript, Vite, SQLite, WebdriverIO, GitHub Actions

## Market applications

### Trading terminals
- Real-time market data with streaming charts
- Multi-window layouts for watchlists, order books, positions
- Keyboard-driven order entry for speed
- Local trade journal and P&L tracking

### Document review
- Side-by-side document comparison and annotation
- Drag-and-drop file ingestion from local filesystem
- Full-text search across local document corpus
- Collaboration overlay with comment threads

### Clinical dashboards
- Patient vitals monitoring with real-time updates
- Multi-panel views for labs, imaging, notes
- Offline access to critical patient data
- HIPAA-compliant local data handling

### Admin tools
- Database browser and query editor
- Log viewer with filtering and search
- Configuration management with diff view
- Multi-environment connection switching
