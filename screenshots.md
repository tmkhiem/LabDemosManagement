# Lab Demo Manager — Feature Screenshots

This document provides visual references for each major feature added or
updated in this release.

---

## 1. Login Page

Standard login for all users (admin & students).

![Login page](https://github.com/user-attachments/assets/4266ca31-114b-4ff5-9f4e-395605370175)

---

## 2. Admin Dashboard

The admin overview now includes **four stat cards** (Student Accounts,
Active Demos, Registered Last 7 Days, **Lab Servers**) and **three quick-link
cards** for the main management areas.

![Admin Dashboard](https://github.com/user-attachments/assets/a929692f-5ce2-4753-86b5-c2290bc93ddf)

---

## 3. Lab Servers Management (`/admin/servers`)

Admins can view, add, edit and delete pre-registered lab servers.
The table shows the friendly **name** and **IP address** for each server.
Only internal LAN IPs (RFC 1918 ranges) are accepted.

![Servers page](https://github.com/user-attachments/assets/bc0938d1-2ce7-432e-b1b9-21bfcc5c5c53)

---

## 4a. Add Server — External IP rejected (frontend validation)

Typing an external IP (e.g. `8.8.8.8`) immediately shows a **red error**
hint: *"✗ Not a private LAN address. External IPs are not allowed."*
The same check is enforced on the backend as a safety net.

![IP validation — invalid external IP](https://github.com/user-attachments/assets/d87d9a87-fdf9-49af-80b1-6cfe8c27468d)

---

## 4b. Add Server — Internal IP accepted (frontend validation)

A valid private address (e.g. `10.0.1.31`) shows a **green** confirmation:
*"✓ Valid internal IP address."*

![IP validation — valid internal IP](https://github.com/user-attachments/assets/0a4f4ab5-e019-4364-a46a-2ce538d41b45)

---

## 5. Demo Report (`/admin/demos`)

Sortable table listing every demo with:

| Column | Detail |
|--------|--------|
| **Demo / Student** | Demo name (bold) with student username below in small text |
| **Path** | Clickable public URL `/username/demo-name` |
| **Hits** | Total access count (indigo badge) |
| **Last Access** | Datetime in **UTC+7** + relative time. An **⚠ amber warning** appears when the last access was more than 30 days ago. Never-accessed demos show *"Never accessed"* in grey. |
| **Actions** | Edit (opens modal with server dropdown) and Delete buttons |

Column headers are clickable to sort ascending/descending.

![Demo Report](https://github.com/user-attachments/assets/9a51ea5e-edc2-4518-9388-0587fa98d749)

---

## 6. Student Dashboard (`/dashboard/`)

Students see their registered demos as cards showing the public URL and
target server/port. Each card has **Edit**, **Activate/Deactivate**, and
**Delete** buttons.

![Student Dashboard](https://github.com/user-attachments/assets/2019c044-ee78-4cf6-a4ed-4e93256ee54b)

---

## 7. Register New Demo — Server Dropdown

Instead of typing a raw URL, students now pick a **server from a dropdown**
(showing friendly name + IP), enter the **port number**, and choose
**HTTP or HTTPS** (self-signed certificates are accepted). The backend
constructs and validates the final URL automatically.

![Register Demo modal with server dropdown](https://github.com/user-attachments/assets/c3b40cc0-5e58-47f7-8643-21202063b23d)

---

## Summary of Changes

| Feature | Where |
|---------|-------|
| `Server` model + admin CRUD | `app/models.py`, `app/admin.py`, `app/templates/admin/servers.html` |
| Seed 5 initial servers (dragon1/2, phoenix1/2/3) | `app/cli.py` (`seed-servers` & `seed-demo-data`) |
| Internal-IP-only validation (FE + BE) | `app/student.py`, `app/admin.py`, `static/app.js` |
| Server dropdown replaces free-text URL in demo forms | `app/templates/student/dashboard.html`, `app/templates/components/demo_card.html` |
| Hit count + last-accessed tracking | `app/models.py`, `app/proxy.py` |
| Demo Report (sortable table, UTC+7, relative time, >30-day warning) | `app/admin.py`, `app/templates/admin/demo_report.html` |
| Admin demo edit / hard-delete from report | `app/admin.py` |
| Updated admin nav (Dashboard, Users, Servers, Demo Report) | `app/templates/base.html` |
| Client-side table sort | `static/app.js` |
