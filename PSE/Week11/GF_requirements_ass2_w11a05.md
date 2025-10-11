# 📋 Project Summary – Loc & Weather Reminder App

## 👥 Team Members
| Role | Name | Responsibilities |
|------|------|------------------|
| **Backend Developer** | **Eduardo JR Ilagan** | FastAPI backend, PostgreSQL DB, reminder CRUD, CI setup, testing & documentation |
| **Android Developer** | **Mark dela Torre** | Android front-end (Compose/Flutter), geofencing logic, notification handling, UI integration |
| **Both (Joint Tasks)** | **Dod & Mark** | Testing, polish, and final release documentation |

---

## 🧾 Epic Overview

| Summary | Description | Epic Name | Epic Link | Status |
|----------|--------------|------------|------------|---------|
| **Reminder Creation & Management** | CRUD for reminders; choose trigger type; notification actions; local persistence. | REM-CORE |  | In Progress |
| **Location Tracking & Geofencing** | Geofence entry/exit handling, debounce, dwell time, accuracy tuning. | GEOFENCE |  | In Progress |
| **Weather Forecast & Rules** | Weather API integration, rule evaluator, caching, offline handling. | WX-RULES |  | Not Started |
| **App Infrastructure** | Local DB, background workers, CI, crash logging. | APP-INFRA |  | In Progress |
| **Polish & Docs** | Permission flows, settings, docs, release notes. | POLISH |  | In Progress |

---

## ⚙️ Functional Requirements

| Summary | Description | Epic Name | Status |
|----------|--------------|------------|---------|
| Create Reminder UI (title, notes, trigger type) | Compose/Flutter screen; validation; empty states. | REM-CORE | In Progress |
| Reminder Notification with actions (Snooze, Done) | System notification channel; action intents; UX copy. | REM-CORE | In Progress |
| Implement weather rule evaluator (pure function) | Rain chance ≥ X% within Y hours; temp/wind thresholds. | WX-RULES | Not Started |
| Map picker & radius selection | Map view; draggable pin; radius ring; default 150m. | GEOFENCE | In Progress |
GEOFENCE | In Progress |
| Debounce and dwell time logic | Avoid duplicate triggers; configurable dwell (e.g., 2 min). | GEOFENCE | In Progress |
| Integrate Open-Meteo API (free) | HTTP c
---

## 🧩 Non-Functional Requirements

| Summary | Description | Epic Name | Status |
|----------|--------------|------------|---------|
| Persist Reminder to local DB (Room/sqflite) | Entities, DAO, repository pattern; migrations. | REM-CORE | In Progress |
| Register geofence and handle enter/exit callbacks | Fused Location Provider + Geofencing API; broadcast receiver. | lient; hourly forecast; model mapping; caching. | WX-RULES | Not Started |
| Background worker to evaluate weather rules | WorkManager/Isolate; interval control; backoff; offline behavior. | WX-RULES | Not Started |
| Set up CI (lint + unit tests) | GitHub Actions; cache; badges in README. | APP-INFRA | In Progress |
| Crash logging & analytics | Firebase Crashlytics; privacy note in README. | APP-INFRA | In Progress |
| Permission rationale flows (foreground + background location) | Explainer screens; deep links to settings; rejection paths. | POLISH | In Progress |
| Settings: units, polling interval, default radius | Preference store; UI toggles; validation. | POLISH | Not Started |
| README + Confluence pages (Architecture, Test Plan, Release Notes) | Concise setup; diagrams; test matrix. | POLISH | In Progress |

---


