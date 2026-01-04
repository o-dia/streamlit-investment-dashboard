# Data Persistence Plan

This document is the single source of truth for building a reliable, futureproof data capture pipeline for the Investment Portfolio Dashboard. It covers the current manual snapshot flow, a robust data model for time series analysis, error handling, broker unification, and the path to full automation. It is written so another agent can implement the system with only this doc and repo context.

---

## Goals and non-goals

### Goals
- Capture portfolio snapshots manually from the Streamlit UI (current phase).
- Store time series data in PostgreSQL for robust analysis and visualization.
- Use broker-provided timestamps with timezone (timestamptz).
- Persist both raw broker payloads and normalized data.
- Support multi-broker (IB now; Schwab later), with clean unification.
- Make the pipeline idempotent and resilient to errors.
- Provide a clear path to automation (cron/systemd) later.

### Non-goals (for now)
- Fully automated scheduled snapshots (deferred).
- Reconstructing transactions from positions.
- Replacing broker truth with derived data.

---

## Core assumptions
- Base currency: GBP.
- Source of truth: broker APIs; we do not fabricate historical trades.
- Manual triggers only for now (Streamlit button).
- Postgres is running locally (today), but will move to Pi later.

---

## Data model (PostgreSQL)

### 1) snapshot_runs
Tracks each manual capture run. One run can include multiple brokers/accounts.
- `run_id` (UUID, PK)
- `trigger_type` (text, e.g. `manual`)
- `triggered_by` (text, optional)
- `started_at` (timestamptz)
- `finished_at` (timestamptz)
- `status` (text: `running`, `success`, `partial`, `fail`)
- `schema_version` (text)
- `app_version` (text, optional)
- `error_summary` (text, nullable)

### 2) broker_accounts
Defines broker accounts known to the system.
- `id` (UUID, PK)
- `broker` (text: `ib`, `schwab`, etc.)
- `broker_account_id` (text)
- `name` (text)
- `base_currency` (text)

### 3) instruments
Broker-specific instrument identifiers.
- `id` (UUID, PK)
- `broker` (text)
- `broker_instrument_id` (text)
- `symbol` (text)
- `name` (text)
- `asset_class` (text)
- `currency` (text)
- `isin` (text, nullable)
- `cusip` (text, nullable)

### 4) instrument_mapping
Maps broker instruments to a global instrument identity.
- `global_instrument_id` (UUID)
- `instrument_id` (UUID, FK -> instruments)
- `mapping_source` (text: `manual`, `heuristic`, `broker`)
- `confidence` (numeric, optional)

### 5) snapshots
Broker- and account-scoped snapshot row.
- `id` (UUID, PK)
- `run_id` (UUID, FK -> snapshot_runs)
- `broker` (text)
- `broker_account_id` (text)
- `asof_ts` (timestamptz)  # broker-provided time
- `snapshot_key` (text, unique)  # idempotency key
- `total_value_local` (numeric)
- `total_value_gbp` (numeric)
- `base_currency` (text, default `GBP`)

### 6) positions
Position rows per snapshot.
- `snapshot_id` (UUID, FK -> snapshots)
- `instrument_id` (UUID, FK -> instruments)
- `quantity` (numeric)
- `price_local` (numeric)
- `market_value_local` (numeric)
- `market_value_gbp` (numeric)
- `fx_rate_id` (UUID, FK -> fx_rates, nullable)
- `cost_basis` (numeric, nullable)
- `unrealized_pnl` (numeric, nullable)

Unique constraint: `(snapshot_id, instrument_id)`.

### 7) fx_rates
FX rates used for conversion.
- `id` (UUID, PK)
- `asof_ts` (timestamptz)
- `source_ccy` (text)
- `target_ccy` (text)
- `rate` (numeric)
- `provider` (text)

### 8) raw_payloads
Raw broker responses for reprocessing.
- `id` (UUID, PK)
- `run_id` (UUID, FK -> snapshot_runs)
- `broker` (text)
- `endpoint` (text)
- `payload_json` (jsonb)
- `received_at` (timestamptz)

### 9) trades (optional, only if broker provides)
- `id` (UUID, PK)
- `broker` (text)
- `broker_trade_id` (text, unique)
- `broker_account_id` (text)
- `instrument_id` (UUID)
- `trade_ts` (timestamptz)
- `quantity` (numeric)
- `price_local` (numeric)
- `amount_local` (numeric)
- `amount_gbp` (numeric)

---

## Idempotency strategy

Goal: If the snapshot process is retried, data must not duplicate.

- `snapshot_key` is deterministic, e.g.:
  - `run_id + broker + broker_account_id + broker_asof_ts`
- `snapshots.snapshot_key` has a unique constraint.
- `positions` uses `(snapshot_id, instrument_id)` unique constraint.
- Writes use upserts with `ON CONFLICT DO NOTHING` or `ON CONFLICT UPDATE`.

---

## Manual snapshot workflow (current)

1. User clicks **Save Snapshot** in Streamlit UI.
2. Create `snapshot_runs` row with `status=running`.
3. For each broker:
   - Fetch summary + positions + fx rates.
   - Store raw JSON in `raw_payloads`.
   - Normalize to canonical model.
   - Write `snapshots`, `positions`, and `fx_rates` in one transaction.
4. If one broker fails, mark run `partial` and keep successful broker data.
5. Update `snapshot_runs` with `finished_at` and status.

---

## Error handling and observability

- Categorize errors: auth, network, rate-limit, parsing, validation, DB.
- Store `error_summary` in `snapshot_runs`.
- Use retries with exponential backoff for transient failures.
- Keep raw payloads for debugging and reprocessing.

---

## Broker unification (IB + Schwab)

- Keep raw broker data separate.
- Use `instrument_mapping` to unify across brokers.
- Aggregation is done in DB views, not by overwriting raw data.

Recommended views:
- `latest_snapshot_per_broker_account`
- `daily_portfolio_value`
- `positions_history`
- `asset_allocation_by_global_instrument`

---

## Future automation (deferred)

### Step 1: Extract snapshot logic into a headless function
- Same code path for UI and automation.
- Input: trigger context; Output: snapshot run + status.

### Step 2: Scheduler on Pi
- Use `cron` or `systemd` timer on the Pi.
- Frequency to be decided later (e.g., hourly or daily).

### Step 3: Monitoring
- Track last success timestamp.
- Add alerts on failure (email, Slack, or push).

---

## Migration plan

1. Build schema in local Postgres.
2. Implement manual snapshot save in Streamlit.
3. Verify time series tables with test data.
4. Add Schwab integration and unify instruments.
5. Move Postgres to Pi and point `DATABASE_URL` to Tailscale IP.
6. Add headless scheduler and alerts.

---

## Implementation checklist

- [ ] Define schema migrations (SQL or ORM).
- [ ] Add `Save Snapshot` button in UI.
- [ ] Implement broker fetch with clean normalization layer.
- [ ] Store raw payloads + normalized data in single transaction.
- [ ] Add idempotency constraints + upsert logic.
- [ ] Add basic logging and error reporting.
- [ ] Build analytics views.
- [ ] Document automation steps for later.
