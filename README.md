# Investment Portfolio Dashboard

A Streamlit-based dashboard that provides a holistic view of investments. 
I created this because I have to check my different investment accounts separately, on my phone, 
but I increasingly want to load ONE app where I view everything together and I can understand and track
how my investments are doing. I have integrated with Charles Schwab and Interactive Brokers, but you can use 
this framework to add more portfolios and it should work all the same - you just need to authenticate with
the relevant brokerage and make sure their APIs support what you need.

## Features

- **Portfolio Overview**: View total portfolio value and performance across all accounts
- **Multi-Broker Support**: Integrate with both Charles Schwab and Interactive Brokers
- **Flexible Views**: Filter by broker or account type
- **Asset Allocation**: Visualize portfolio allocation by security
- **Performance Metrics**: Track unrealized P/L, returns, and more

## Screenshots

[Coming soon]

## Requirements

- Python 3.8+
- Streamlit
- PostgreSQL (for persistence)
- ngrok (for OAuth authentication)
- API credentials for Charles Schwab and/or Interactive Brokers

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/o-dia/streamlit-investment-dashboard.git
   cd streamlit-investment-dashboard
   ```

2. Create and activate your conda environment:
   ```
   conda activate streamlit-dashboard
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your credentials:
   ```
   SCHWAB_CLIENT_ID=your_client_id_here
   SCHWAB_CLIENT_SECRET=your_client_secret_here
   SCHWAB_REDIRECT_URI=your_ngrok_url_here/callback
   
   # Postgres
   DATABASE_URL=postgres://user:password@host:5432/portfolio_db

   # For Interactive Brokers (optional)
   IB_CLIENT_ID=your_ib_client_id
   IB_GATEWAY_PORT=4001
   IB_HOST=127.0.0.1
   ```

## Database Setup (Postgres)

These steps are run by you on the machine hosting Postgres (local laptop or the Pi). The app reads `DATABASE_URL` from `.env`.

### A) Local setup (laptop)

1. Install Postgres and start the service.

2. Create the database (name is `investment_dashboard`):
   ```
   createdb investment_dashboard
   ```

   If you want to create a dedicated app user instead of reusing your existing role:
   ```
   psql -U postgres
   CREATE USER investment_app WITH PASSWORD 'REPLACE_ME';
   CREATE DATABASE investment_dashboard OWNER investment_app;
   \q
   ```

3. Set `DATABASE_URL` in your `.env`:
   ```
   DATABASE_URL=postgres://<db_user>:<db_password>@localhost:5432/investment_dashboard
   ```
   Example if your Postgres user is `Omar`:
   ```
   DATABASE_URL=postgres://Omar:<your_password>@localhost:5432/investment_dashboard
   ```

4. Verify the connection:
   ```
   psql -h localhost -U Omar -d investment_dashboard
   \conninfo
   ```

### B) Raspberry Pi setup (SSH)

1. Install Postgres on the Pi:
   ```
   sudo apt update
   sudo apt install postgresql -y
   ```

2. Create the database and user on the Pi:
   ```
   sudo -u postgres psql
   CREATE USER investment_app WITH PASSWORD 'REPLACE_ME';
   CREATE DATABASE investment_dashboard OWNER investment_app;
   \q
   ```

3. Allow connections from your laptop (Tailscale recommended):
   - Edit `postgresql.conf` and set:
     ```
     listen_addresses = 'localhost,<pi-tailscale-ip>'
     ```
   - Edit `pg_hba.conf` and add:
     ```
     host    investment_dashboard    investment_app    <laptop-tailscale-ip>/32    scram-sha-256
     ```

4. Restart Postgres:
   ```
   sudo systemctl restart postgresql
   ```

5. Set `DATABASE_URL` on your laptop:
   ```
   DATABASE_URL=postgres://investment_app:REPLACE_ME@<pi-tailscale-ip>:5432/investment_dashboard
   ```

## Usage (Local)

1. (Optional, Schwab) Start ngrok to create a tunnel for OAuth.
   - If you set up the LaunchAgent (see below), ngrok will already be running in the background.
   - Otherwise run:
     ```
     ngrok http 8501
     ```

2. (Optional, Schwab) Update your `.env` file with the ngrok URL
   - ngrok URLs change each time you run it; update both `.env` and the Schwab developer portal redirect URL to match.

3. (IB) Start the Interactive Brokers Client Portal API Gateway and log in.

4. Run the app:
   ```
   streamlit run app.py
   ```

5. Open your browser to http://localhost:8501

6. Navigate to the Authentication tab to connect your brokerage accounts

## ngrok as a Background Service (macOS LaunchAgent)

If you use Schwab OAuth often, you can run ngrok as a macOS LaunchAgent so it runs in the background and survives terminal closes.

### What changes in your workflow
- You no longer need to keep a terminal open running `ngrok http 8501`.
- The tunnel starts at login and is kept alive by macOS.
- Your public URL stays the same as long as the background process stays up.

### How to check current ngrok status
- Is it running?
  ```
  launchctl list | grep ngrok
  ```
  The first column is the PID of the running ngrok process.

- What is the current public URL?
  - Open the local web UI: `http://127.0.0.1:4040`
  - Or run:
    ```
    curl -s http://127.0.0.1:4040/api/tunnels
    ```
    Look for `public_url` in the output.
  - One-liner (prints just the URL if `jq` is installed):
    ```
    curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url'
    ```

### What if the public URL changes?
- On the free ngrok plan, URLs can change if ngrok restarts or the session drops.
- For a stable URL, use a reserved domain (paid ngrok plan).
- If you want notifications on URL changes, add a small polling script to alert you when `public_url` changes.

## Step-by-Step Terminal Commands (Local)

```
cd /Users/Omar/Coding/Python/Streamlit
conda activate streamlit-dashboard
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your credentials, then run:

```
streamlit run app.py
```

## Development Status

This project is currently in development. Authentication with Charles Schwab API is pending resolution.

## Technologies Used

- Python
- Streamlit
- Plotly
- Pandas
- OAuth for API authentication
