# Wattics Data Pipeline

A Python pipeline to collect, merge, and analyze energy meter consumption and cost data from the Wattics API. The project fetches meter metadata, retrieves consumption and cost time series, merges the data, computes weekly KPIs, detects anomalies, forecasts next-week consumption per site, generates visual dashboards (Plotly HTML), and can produce text reports.

## Features

- Fetches meter metadata, consumption, and cost data from Wattics
- Cleans and merges consumption and cost into a single dataset
- Aggregates to weekly KPIs (consumption, cost, cost-per-kWh, WoW change)
- Detects anomalies using z-score and week-over-week thresholds
- Forecasts next-week consumption per site with simple lag-based models (linear / random forest)
- Generates an interactive Plotly HTML dashboard and text reports
- Sends email reports via Gmail SMTP (optional)

## Repository layout

- `main.py` — full pipeline orchestrator (fetch, merge, KPIs, anomalies, forecasts, reporting)
- `reduced_data_collection.py` — filtered pipeline for a small set of orgs/sites
- `api/` — Wattics API client wrappers (organizations, sites, meters, consumption, costs)
- `Transformations/aggregation.py` — merging and cleaning logic
- `kpis/` — KPI aggregation and ranking logic
- `analysis/` — anomaly detection and site ranking
- `forecasting/` — forecasting and evaluation utilities
- `dashboard/` — Plotly HTML dashboard builder
- `report/` — report generation (LLM-backed generators included)
- `load/` — email/report delivery utilities

## Requirements

- Python 3.10+
- Recommended: create and use a virtual environment

Suggested dependencies (add to `requirements.txt`):

```
python-dotenv
pandas
numpy
plotly
scikit-learn
openai
```

## Setup

1. Create a virtual environment and activate it:

Windows (CMD):

```bash
python -m venv venv
venv\Scripts\activate
```

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root (this file MUST NOT be committed). Example variables:

```
API_TOKEN=your_wattics_api_token
GMAIL_SENDER_EMAIL=youremail@gmail.com
GMAIL_APP_PASSWORD=your_app_password
RECEIVER_EMAIL=receiver@example.com
OPENAI_API_KEY=your_openai_api_key
```

You can add `.env.example` to the repo with placeholder values to guide contributors.

## Usage

- Run the full pipeline (fetch all meters for configured orgs):

```bash
python main.py
```

- Run the filtered pipeline (preconfigured organizations/sites):

```bash
python reduced_data_collection.py
```

Outputs are written to CSV and HTML files in the project root (these are ignored by `.gitignore`):

- `meter_consumption_data_False.csv`
- `cost_data.csv`
- `merged_consumption_costs.csv`
- `dataset.csv` (weekly KPIs)
- `dataset_with_anomalies.csv`
- `anomalies.csv`
- `forecasts.csv`
- `forecast_evaluation.csv`
- `energy_dashboard.html`
- `summary_report.txt`

## Security & privacy

- Keep `.env` and any credentials out of the repository. The included `.gitignore` already excludes `.env`, `venv`, and generated CSV/TXT files.

## License

Add a `LICENSE` file (e.g., MIT or Apache-2.0) if you plan to publish this project publicly.

## Contributing

- If you want others to contribute, add a `CONTRIBUTING.md` with guidelines and tests.

## Contact

For questions about this repo, open an issue or contact the maintainer.
