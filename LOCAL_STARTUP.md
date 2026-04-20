# Local Startup Runbook

This is the shortest repo-specific path to get the dashboard running locally after some time away.

Use this file instead of piecing together `README.md`, `GettingStartedWithIB.md`, and old terminal history.

## What Should Be Running

For normal local use, there are three moving parts:

1. Postgres
2. Interactive Brokers Client Portal Gateway
3. The Streamlit app

`ngrok` is separate. It only matters for Schwab OAuth, and on this laptop it is configured as a background macOS LaunchAgent, so you do not usually keep a terminal open for it.

## Current Local Assumptions

These are the values the app currently expects:

- Streamlit app: `http://localhost:8501`
- Postgres: `localhost:5432`
- Database name: `investment_dashboard`
- IB Gateway host: `127.0.0.1`
- IB Gateway port: `5002`
- Recommended IB Gateway install directory: `~/Applications/clientportal.gw`

The IB port is `5002` because the app expects `https://127.0.0.1:5002`.

## Before You Start

From the repo root:

```bash
cd /Users/Omar/Coding/Python/Streamlit
conda activate streamlit-dashboard
python -m pip install -r requirements.txt
```

Check `.env` before launching anything:

- `DATABASE_URL` should point to `investment_dashboard` on `localhost:5432`
- `IB_HOST` should be `127.0.0.1`
- `IB_GATEWAY_PORT` should be `5002`
- `IB_GATEWAY_DIR` should point to your local Client Portal Gateway install if you are not using `~/Applications/clientportal.gw`
- `SCHWAB_REDIRECT_URI` should exactly match the current ngrok public URL if you want Schwab auth to work

## Recommended Gateway Layout

Keep the IB Client Portal Gateway outside this repo so logs, runtime files, and keystores never mix with project files.

Recommended path:

```text
~/Applications/clientportal.gw
```

If you already have a local copy in this repo from the older setup, move it once to that location, then keep starting it from the repo root with:

```bash
./scripts/start_ib_gateway.sh
```

The launcher script reads `IB_GATEWAY_DIR` from your shell or `.env`. If that is missing, it falls back to `~/Applications/clientportal.gw`.

## Terminal Layout

Open three terminals.

### Terminal 1: Run The App

```bash
cd /Users/Omar/Coding/Python/Streamlit
conda activate streamlit-dashboard
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

If you just want to confirm the UI loads, the app can open without broker connections.

### Terminal 2: Start Interactive Brokers Gateway

```bash
cd /Users/Omar/Coding/Python/Streamlit
./scripts/start_ib_gateway.sh
```

What to expect:

- the gateway should listen on `https://127.0.0.1:5002`
- you may need to open that URL in a browser and log in before the app can connect

Useful checks if you reopened VS Code and are not sure whether it is still running:

```bash
lsof -nP -iTCP:5002 -sTCP:LISTEN
pgrep -af 'clientportal|GatewayStart'
```

Once the gateway is authenticated:

1. Go to the app
2. Open the `Authentication` tab
3. Click `Open IB Gateway login in a new tab`
4. Complete the login in the gateway tab
5. Return to the app tab and wait for the app to auto-connect

### Terminal 3: Start Or Verify Postgres

Postgres normally runs as a background service, so this terminal is mostly for checks and one-off DB commands.

Start or verify the service:

```bash
brew services list | grep postgres
brew services start postgresql@16
```

List databases:

```bash
psql -h localhost -U Omar -l
```

If `investment_dashboard` does not exist yet, create it:

```bash
createdb -h localhost -U Omar investment_dashboard
```

Connect to it:

```bash
psql -h localhost -U Omar -d investment_dashboard
```

Useful commands inside `psql`:

```sql
\conninfo
\dt
\q
```

Important: the app creates its tables lazily. If the database exists but has no tables yet, run the app and click `Store snapshot` once after loading portfolio data.

## ngrok And Schwab OAuth

This laptop has a LaunchAgent configured at:

```text
~/Library/LaunchAgents/com.omar.ngrok.plist
```

It runs:

```bash
ngrok start streamlit
```

That means you do not need a dedicated terminal for ngrok in normal use.

### Check Whether ngrok Is Running

```bash
launchctl list | grep ngrok
```

If you see `com.omar.ngrok`, the LaunchAgent is loaded.

You can also check the tunnel API:

```bash
curl -s http://127.0.0.1:4040/api/tunnels
```

Look for `public_url`.

### Check The Current Public URL

```bash
curl -s http://127.0.0.1:4040/api/tunnels
```

If you have `jq` installed:

```bash
curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```

### Restart ngrok If Needed

If the LaunchAgent is loaded but the tunnel looks stale or unavailable:

```bash
launchctl kickstart -k gui/$(id -u)/com.omar.ngrok
```

If that does not recover it:

```bash
launchctl unload ~/Library/LaunchAgents/com.omar.ngrok.plist
launchctl load ~/Library/LaunchAgents/com.omar.ngrok.plist
```

Then re-check:

```bash
launchctl list | grep ngrok
curl -s http://127.0.0.1:4040/api/tunnels
```

### Important Caveat About The Schwab Callback URL

Your current ngrok setup keeps the tunnel running in the background, but it does not guarantee a permanent public URL by itself.

The current ngrok config uses a named tunnel called `streamlit`, but it does not specify a reserved domain. That means:

- the URL can stay the same for long stretches if ngrok keeps running
- the URL can still change if ngrok restarts or the session resets

So before using Schwab auth, always verify that:

1. ngrok is running
2. the current `public_url` matches `SCHWAB_REDIRECT_URI` in `.env`
3. the same callback URL is registered in the Schwab developer portal

If those three do not match exactly, Schwab OAuth will fail.

## Minimal Bring-Up Checklist

Use this when you want the shortest path:

1. Start Postgres: `brew services start postgresql@16`
2. Confirm the DB exists: `psql -h localhost -U Omar -l`
3. Start IB Gateway: `./scripts/start_ib_gateway.sh`
4. Check ngrok URL: `curl -s http://127.0.0.1:4040/api/tunnels`
5. Make sure `.env` has the same `SCHWAB_REDIRECT_URI`
6. Start the app: `streamlit run app.py`
7. Open `http://localhost:8501`

## What To Check If Something Fails

If the app opens but DB Explorer is empty:

- confirm `investment_dashboard` exists
- confirm `DATABASE_URL` points to it
- remember the schema is only created after `Store snapshot`

If Interactive Brokers will not connect:

- confirm the gateway is running on `https://127.0.0.1:5002`
- if needed, check the process with `pgrep -af 'clientportal|GatewayStart'`
- expect the browser to warn about the gateway's self-signed localhost certificate
- log in to the gateway in the browser first
- then return to the app tab and give it a few seconds to auto-connect
- if needed, use the manual `Connect to Interactive Brokers now` fallback button

If Schwab auth breaks:

- confirm ngrok is running
- confirm the current `public_url`
- confirm `.env` uses that exact URL
- confirm Schwab developer settings use that exact URL
