# Linux Log Monitoring GUI (PyQt5 + SSH)

A lightweight PyQt5 desktop GUI that connects to a remote Linux host via SSH and displays basic system status and security/log information. It periodically runs Linux commands and reads key log files, then shows results in tables and can export all records to a text file.

## What it does

From the code:
- Connects to a remote Linux server using `paramiko` SSH.:contentReference[oaicite:3]{index=3}
- Periodically fetches:
  - CPU / memory / process list (via `top -b -n 1`):contentReference[oaicite:4]{index=4}
  - Current login sessions (via `who`):contentReference[oaicite:5]{index=5}
  - Sudo-related entries in `/var/log/auth.log` (grep sudo):contentReference[oaicite:6]{index=6}
  - Failed login history (via `lastb`, reading `/var/log/btmp`):contentReference[oaicite:7]{index=7}
- Parses `auth.log` entries and (optionally) does GeoIP lookups for IP addresses using a GeoLite2 `.mmdb` database.:contentReference[oaicite:8]{index=8}:contentReference[oaicite:9]{index=9}
- Monitors `auth.log` for new lines and triggers alerts when it finds “Failed password” or “Accepted password”.:contentReference[oaicite:10]{index=10}
- Exports all table contents into a text file when clicking the Save button.:contentReference[oaicite:11]{index=11}

## Project structure

- `run.py` — GUI entry point (creates the Qt app and shows the window).:contentReference[oaicite:12]{index=12}
- `homepage.py` — main GUI logic (SSH connection, timers, log parsing, monitoring, export).:contentReference[oaicite:13]{index=13}
- `UI/ui.py` — generated PyQt UI code (imported by `homepage.py`).:contentReference[oaicite:14]{index=14}
- `main.py` — simple SSH test script (example command: grep sudo in auth.log).:contentReference[oaicite:15]{index=15}

## Requirements

Python 3.8+ recommended.

Install dependencies:
```bash
pip install -r requirements.txt
