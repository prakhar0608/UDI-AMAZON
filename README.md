# Amazon Ads SP Campaign Reporter

Python app that pulls **Sponsored Products** campaign reports (last **5** calendar days, **daily** rows, **1-day** sales attribution), computes **RoAS** and **ACoS**, pivots metrics into wide columns per day, saves **CSV** and **XLSX** under `data/processed/`, and provides a **Streamlit** UI with pagination and downloads.

## Prerequisites

- Python 3.11+
- Amazon Ads developer application with **LWA** client id/secret and **refresh token** for the Advertising API
- Advertising API access to **Reporting v3**

Exact `reportTypeId` and report **column** names can change; this project uses `spCampaigns` with `DAILY` time unit. If Amazon updates schemas, adjust `src/amazon_ads_app/parse_report.py` column aliases.

## Setup (Windows PowerShell)

```powershell
cd c:\Users\dell\Desktop\amazon
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Copy environment variables:

```powershell
copy .env.example .env
```

Edit `.env` with `LWA_CLIENT_ID`, `LWA_CLIENT_SECRET`, and `LWA_REFRESH_TOKEN` (client id/secret alone cannot call the API; the refresh token is required for access tokens). Use **single-line** values only (no line breaks inside a value). Avoid wrapping values in quotes unless the whole value is quoted; stray quotes or newlines can break the `Authorization: Bearer …` header and cause **403** errors from Amazon’s API gateway.

Optional: set `AMAZON_ADS_DEBUG_AUTH=1` to log **safe** token metadata (length + SHA-256 prefix) when tokens refresh — never the raw token.

### Troubleshooting auth (403 on reports)

1. Run **`amazon-ads-fetch --validate-auth`** — if **no** region returns OK, fix LWA credentials and refresh token.
2. In Streamlit, use **Validate API auth** after picking a profile — checks unscoped and scoped List Profiles.
3. Ensure tokens are normalized: the app strips env vars and validates access tokens (no embedded whitespace).

**Accounts (two options):**

1. **Recommended:** In the Streamlit sidebar, click **Refresh accounts from API**. The app calls the List Profiles endpoint on each regional host (NA, EU, FE), merges results, and saves `data/cache/profiles_cache.json`. Profiles that share the same advertiser account (Amazon `accountInfo.id` or name) are **grouped** under one entry; pick **Region / profile** when a group has multiple regions. Use **Search** to filter by name, region, or profile id.
2. **Manual:** Copy `config\profiles.yaml.example` to `config\profiles.yaml`, fill in **profile id**, **region**, and **display_name**, then enable **Use manual config/profiles.yaml** in the sidebar. Optional **`account_group`** groups rows the same way as API discovery.

If you upgrade to a version that uses profile timezone/currency metadata, run **Refresh accounts from API** once so cached profiles include the new fields.


## Virtual Enviornment Command
amazon\Scripts\activate

## Run UI

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run streamlit_app.py
```

## CLI (no browser)

After `pip install -e .`:

```powershell
# Discover profiles (JSON on stdout)
amazon-ads-fetch --discover

# Refresh the same cache file the UI uses
amazon-ads-fetch --refresh-cache

# Validate LWA token against List Profiles in NA/EU/FE (exit 0 if any region succeeds)
amazon-ads-fetch --validate-auth

# Fetch report: profile id must exist in discovery cache or manual profiles.yaml
amazon-ads-fetch --profile-id 1234567890

# Optional: cap how long to poll for async report completion (minutes)
amazon-ads-fetch --profile-id 1234567890 --max-poll-minutes 30

# Resume a timed-out run: same report id + raw folder from the run (contains report_job.json)
amazon-ads-fetch --profile-id 1234567890 --resume-report-id REPORT_ID --resume-raw-dir data\\raw\\NA\\myprofile\\20250101T120000Z_ab12cd34
```

Each CLI/UI run fetches **one** selected profile only. Polling uses a staged schedule with jitter; if the report stays pending past `--max-poll-minutes` (default in `report_config.py`), the app raises a timeout with the `report_id` so you can resume without creating a duplicate report.

## Date range

The pipeline uses the last **5** calendar days in **UTC**, inclusive of the end date (see `pipeline.py`).

## Logs

Rotating logs: `logs/app.log` (gitignored). Configure in `logging_setup.py`.

## Tests

```powershell
pytest
```
