# Investment Portfolio Dashboard

A Streamlit dashboard for viewing investment accounts from multiple brokers in one place.

The current app supports:

- Charles Schwab
- Interactive Brokers
- Postgres-backed snapshot storage

The goal is to make it easier to see total portfolio value, holdings, allocation, and recent snapshots without jumping between broker apps.

## Features

- Combined portfolio view across supported brokers
- Per-account and per-position breakdowns
- Asset allocation charts
- Manual snapshot storage in Postgres
- Read-only DB Explorer inside the Streamlit app

## Tech Stack

- Python 3.11
- Streamlit
- Plotly
- Pandas / NumPy
- PostgreSQL
- Charles Schwab OAuth
- Interactive Brokers Client Portal API Gateway

## Prerequisites

Install these before starting:

- Conda or Miniconda
- Python 3.11
- PostgreSQL running locally
- `ngrok` if you want to use Schwab OAuth
- Interactive Brokers Client Portal API Gateway if you want IB data

## Clone And Install

```bash
git clone https://github.com/o-dia/streamlit-investment-dashboard.git
cd streamlit-investment-dashboard
conda env create -f environment.yml
conda activate streamlit-dashboard
```

If the environment already exists and you want to sync it with the repo:

```bash
conda env update -n streamlit-dashboard -f environment.yml
conda activate streamlit-dashboard
```

## Configure Environment Variables

Create a `.env` file in the project root with values like these:

```env
SCHWAB_CLIENT_ID=your_client_id_here
SCHWAB_CLIENT_SECRET=your_client_secret_here
SCHWAB_REDIRECT_URI=https://your-ngrok-url.ngrok-free.app

IB_HOST=127.0.0.1
IB_GATEWAY_PORT=5002
IB_GATEWAY_DIR=/Applications/clientportal.gw

DATABASE_URL=postgres://<db_user>:<db_password>@localhost:5432/investment_dashboard
```

Notes:

- `SCHWAB_REDIRECT_URI` must exactly match the URL registered in the Schwab developer portal.
- The app expects the IB Client Portal Gateway on `https://127.0.0.1:5002`.
- `IB_GATEWAY_DIR` is optional and is used by the repo launcher script, not by the Streamlit app itself.
- The app reads `DATABASE_URL` directly from `.env`.

## Set Up Postgres

Start PostgreSQL using the method that matches your install. For Homebrew:

```bash
brew services start postgresql@16
```

Create the app database:

```bash
createdb investment_dashboard
```

Verify you can connect:

```bash
psql -h localhost -U <db_user> -d investment_dashboard
```

## Run The App

Start Streamlit:

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

The app can load even if no broker is connected yet.

## Connect Charles Schwab

If you want Schwab data:

1. Start `ngrok` against port `8501`.
2. Copy the current `public_url`.
3. Set `SCHWAB_REDIRECT_URI` in `.env` to that exact URL.
4. Update the same callback URL in the Schwab developer portal.
5. Open the app and use the `Authentication` tab to authorize Schwab.

Example:

```bash
ngrok http 8501
curl -s http://127.0.0.1:4040/api/tunnels
```

## Connect Interactive Brokers

If you want Interactive Brokers data:

1. Install the Client Portal Gateway outside this repo, ideally at `/Applications/clientportal.gw`.
2. Start it from the repo root with:

```bash
./scripts/start_ib_gateway.sh
```

3. If you installed it somewhere else, set `IB_GATEWAY_DIR` in `.env` first.
4. In the app, use `Open IB Gateway login in a new tab`.
5. Expect a browser warning about the gateway's self-signed localhost certificate.
6. Complete the login in the gateway tab.
7. Return to the app tab and let it auto-connect.

The helper script defaults to:

```text
/Applications/clientportal.gw
```

That gateway should listen on:

```text
https://127.0.0.1:5002
```

If you already have a local gateway copy inside the repo from older setup steps, move it out of the repo and keep using the launcher script from the project root.

## Returning To The Project Later

This README is meant to help new users clone and run the project for the first time.

If you are coming back to this repo on the original development machine and want the exact local run order, terminal layout, ngrok checks, gateway checks, and service commands, use:

- [LOCAL_STARTUP.md](LOCAL_STARTUP.md)

That file is the project-specific operator runbook.

## Database Behavior

The app creates its Postgres tables lazily the first time you store a snapshot.

That means:

- a newly created `investment_dashboard` database may start empty
- tables appear after you load portfolio data and click `Store snapshot`
- the `DB Explorer` tab is a convenient read-only way to inspect stored tables and rows

## Development Status

This project is still evolving. Broker authentication and data-fetching flows may need refinement as upstream APIs change.
