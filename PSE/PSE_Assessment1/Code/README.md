Dod’s Cars — Car Rental System

A small, object-oriented car-rental app. Runs as a Windows CLI (single .exe) or straight from Python. Uses SQLite. Covers registration/login, availability, bookings, approvals/rejections, maintenance, and a lightweight analytics dashboard.

1 What is this?

A small, object-oriented car-rental app. Runs as a Windows CLI (single .exe) or straight
from Python. Uses SQLite. Covers registration/login, availability, bookings,
approvals/rejections, maintenance, and a lightweight analytics dashboard.

2 Features

Users & roles: customer and admin (role-gated actions)

Availability: date-range search that respects existing bookings and maintenance

Bookings: create pending, fee snapshot, status tracking

Admin: approve or reject bookings, manage cars

Maintenance: open/close windows (blocks availability while open)

Analytics (MVP): Top Users, Top Cars, Maintenance cost & downtime

Acceptance evidence: generates .txt + wide .png snapshots per Use Case (UC01–UC15)

3 Requirements

Windows 10/11 (prebuilt .exe)

Or Python 3.10+ if running from source

No external services; SQLite is bundled

4 Database location & override

Default DB lives under the current user’s application data (created on first run).

To point the app to a specific DB file (PowerShell):

$env:DODSCARS_DB="C:\Data\dodscars.sqlite"

5 Seeder / Demo data (read me first)

A dedicated Seeder executable is included. It fills the database with three years of demo data (users, cars, bookings across pending/approved/rejected, and maintenance windows). This is ideal for demos, analytics, and acceptance screenshots.

Important order:

1. Run the Car Rental app once first (DodsCars.exe). This creates the database and the initial admin account.
2. Then, if demo data is needed, just double-click the seeder executable (DodsCars_Seeder.exe). No command line required.

What the seeder does

- Loads a realistic 3-year dataset (users, cars, bookings with mixed statuses, maintenance windows).
- Leaves your admin account in place (change the password after first login).
-Safe for demos and analytics; avoid running on a live/production DB.

Targeting a different DB (optional):
If a different database file should be used, set it before running the app and seeder:

$env:DODSCARS_DB="C:\Data\dodscars.sqlite"

Quick Start (reordered)

1. Run the app once: double-click DodsCars.exe (initializes DB and admin).
2. (Optional) Seed demo data: double-click DodsCars_Seeder.exe.
3. Open the app again: explore availability, create/approve bookings, and view analytics.
4. (Optional) Generate acceptance evidence: run DodsCars_UCs.exe (or python scripts\uc_scenarios.py) to produce .txt/.png snapshots under .artifacts\.

6 Release notes (template)

Dod’s Cars vYYYY.MM.DD
- New: <feature>
- Change: <refactor/fix>
- Fix: <bug id/description>

Notes:
- Evidence attached: ALL_UC_transcript.png
- DB compatibility: additive only (no destructive migration)

License (MIT)

MIT License

Copyright (c) 2025 Eduardo JR Ilagan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Copyright (c) 2025 Eduardo JR Ilagan
Licensed under the MIT License. See LICENSE for details.
