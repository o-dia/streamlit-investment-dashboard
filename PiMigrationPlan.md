# Raspberry Pi Migration Plan

## Goals
- Host PostgreSQL and Streamlit on a Raspberry Pi (always on).
- Keep IB Gateway on the laptop for now (more reliable).
- Use Tailscale + SSH for secure remote access.
- Persist portfolio snapshots, FX rates, and metadata for analytics.

---

## Phase 0: Prep (when back home)
1) Power and network
   - Ensure the Pi is on reliable power (ideally UPS).
   - Connect to a stable network (Ethernet preferred).

2) Update OS and tools
   - Update Pi packages:
     ```
     sudo apt update && sudo apt upgrade -y
     ```

3) Confirm OS version
   ```
   cat /etc/os-release
   ```

---

## Phase 1: Tailscale + SSH
1) Install Tailscale on the Pi
   ```
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

2) Verify the Pi appears in your Tailscale admin page
   - https://login.tailscale.com/admin/machines

3) SSH in from your laptop
   ```
   ssh <pi-user>@<tailscale-ip>
   ```

4) Harden SSH
   - Use SSH keys (disable password login if possible).
   - Keep a local access method for emergencies.

---

## Phase 2: PostgreSQL on the Pi (apt)
1) Install Postgres
   ```
   sudo apt update
   sudo apt install postgresql -y
   ```

2) Create DB and user
   ```
   sudo -u postgres psql
   CREATE USER portfolio_app WITH PASSWORD 'REPLACE_ME';
   CREATE DATABASE portfolio_db OWNER portfolio_app;
   \q
   ```

3) Bind Postgres to localhost and Tailscale IP
   - Edit `postgresql.conf` (path varies):
     ```
     sudo nano /etc/postgresql/*/main/postgresql.conf
     ```
     Set:
     ```
     listen_addresses = 'localhost,<pi-tailscale-ip>'
     ```

4) Restrict access via `pg_hba.conf`
   ```
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   ```
   Add a rule for your laptop Tailscale IP:
   ```
   host    portfolio_db    portfolio_app    <laptop-tailscale-ip>/32    scram-sha-256
   ```

5) Restart Postgres
   ```
   sudo systemctl restart postgresql
   ```

6) Test from laptop
   ```
   psql "postgres://portfolio_app:REPLACE_ME@<pi-tailscale-ip>:5432/portfolio_db"
   ```

---

## Phase 3: App -> DB Integration (laptop app -> Pi DB)
1) Add to `.env` on laptop:
   ```
   DATABASE_URL=postgres://portfolio_app:REPLACE_ME@<pi-tailscale-ip>:5432/portfolio_db
   ```

2) Add DB schema and snapshot writer
   - Create minimal tables:
     - `snapshots` (ts, total_value_gbp, total_value_usd)
     - `positions` (snapshot_id, symbol, qty, base_currency, gbp_value, usd_value, asset_class)
     - `fx_rates` (ts, source, target, rate)
   - Write snapshot on refresh.

3) Validate
   - Click refresh in Streamlit.
   - Confirm snapshot rows in Postgres.

---

## Phase 4: Streamlit on the Pi
1) Clone repo on Pi
   ```
   git clone <repo-url>
   cd <repo>
   ```

2) Create venv and install dependencies
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3) Create `.env` on Pi
   ```
   DATABASE_URL=postgres://portfolio_app:REPLACE_ME@localhost:5432/portfolio_db
   IB_GATEWAY_PORT=5001
   IB_HOST=127.0.0.1
   ```

4) Run Streamlit manually (test)
   ```
   streamlit run app.py
   ```

5) Optional: systemd service (always on)
   - Create a systemd unit to run Streamlit on boot.

---

## Phase 5: Snapshot Scheduling
If IB Gateway stays on the laptop:
- Schedule a local job on the laptop to hit the Streamlit app or a separate snapshot script.
- The Pi DB will still store the data.

If IB Gateway moves to the Pi:
- Schedule a cron job on the Pi to run a snapshot script.

---

## Phase 6: IB Gateway on the Pi (optional, risky)
Why it is tricky:
- Requires Java + GUI + browser login + 2FA.
- Not officially supported on ARM.
- Session can expire and require manual re-login.

If you want to try it later:
- Install Java 11.
- Install a lightweight desktop + VNC.
- Run the gateway and monitor session health.

---

## Security Checklist
- Postgres: bind to localhost + Tailscale IP only.
- Restrict `pg_hba.conf` to your laptop Tailscale IP.
- Use strong DB password.
- Keep `.env` private.

---

## Rollback and Backup
- Backup: `pg_dump portfolio_db > backup.sql`
- Restore: `psql portfolio_db < backup.sql`

---

## What Runs Continuously (recommended for now)
- Pi: Postgres + Streamlit
- Laptop: IB Gateway (until moved later)
