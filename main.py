import os
from pathlib import Path
from dotenv import load_dotenv

from api.list_organization import WatticsOrganizationClient
from api.sites import WatticsSiteClient
from api.meters import WatticsMeterClient
from api.consumption import WatticsConsumptionClient
from api.costs import WatticsCostClient

from Transformations.aggregation import DataMerger
from kpis.kpi_builder import KPIBuilder
from analysis.site_ranking import SiteRanking
from analysis.anomaly_detector import AnomalyDetector
from forecasting.site_forecaster import SiteForecaster
from forecasting.forecast_evaluator import ForecastEvaluator
from report.insight_report_generator import InsightReportGenerator

from load.mail import EmailReportSender
from dashboard.html_dashboard_generator import HTMLDashboardGenerator

# =========================
# Load environment variables
# =========================

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# =========================
# Pipeline configuration
# =========================

ORGANIZATION_NAMES = [
    "Food Corp.",
    "Best Resorts Hotels"
]

BASE_DIR = Path(__file__).resolve().parent

CONSUMPTION_FILE = BASE_DIR / "meter_consumption_data_False.csv"
COST_FILE = BASE_DIR / "cost_data.csv"
MERGED_FILE = BASE_DIR / "merged_consumption_costs.csv"
WEEKLY_KPIS_FILE = BASE_DIR / "dataset.csv"
LEGACY_WEEKLY_KPIS_FILE = BASE_DIR / "weekly_kpis.csv"
ANOMALIES_FILE = BASE_DIR / "anomalies.csv"
DATASET_WITH_ANOMALIES_FILE = BASE_DIR / "dataset_with_anomalies.csv"
FORECASTS_FILE = BASE_DIR / "forecasts.csv"
FORECAST_EVALUATION_FILE = BASE_DIR / "forecast_evaluation.csv"
SUMMARY_REPORT_FILE = BASE_DIR / "summary_report.txt"
CHART_FILE = BASE_DIR / "trend_anomaly_forecast_chart.png"
HTML_DASHBOARD_FILE = BASE_DIR / "energy_dashboard.html"

START_YEAR = 2014
START_MONTH = 1
END_YEAR = 2027
END_MONTH = 12


# =========================
# Validation
# =========================

def validate_environment():
    if API_TOKEN is None:
        raise ValueError("API_TOKEN is not set.")
    print("Environment validated.")


# =========================
# Get all organizations
# =========================

def get_target_organizations():
    org_client = WatticsOrganizationClient(API_TOKEN)

    organizations = []

    for name in ORGANIZATION_NAMES:
        org = org_client.get_organization_by_name(name)
        if org:
            organizations.append(org)
        else:
            print(f"Skipping missing organization: {name}")

    if not organizations:
        raise ValueError("No valid organizations found.")

    return organizations


# =========================
# Get full metadata
# =========================

def collect_meter_metadata(organizations):
    site_client = WatticsSiteClient(API_TOKEN)
    meter_client = WatticsMeterClient(API_TOKEN)

    all_meter_ids = []
    all_metadata = []

    for org in organizations:
        org_id = org["id"]
        org_name = org["name"]

        print(f"\nProcessing organization: {org_name}")

        sites = site_client.get_sites_for_organization(org_id)

        electricity_meters = meter_client.get_electricity_meters_for_sites(
            organization_id=org_id,
            sites=sites
        )

        for meter in electricity_meters:
            meter_id = meter["id"]

            all_meter_ids.append(meter_id)

            all_metadata.append({
                "meter_id": meter_id,
                "organization_id": org_id,
                "organization_name": org_name,
                "site_id": meter.get("site_id"),
                "site_name": meter.get("site_name")
            })

    return all_meter_ids, all_metadata


def fetch_consumption_data(meter_ids):
    print("\nFetching consumption data for target meters...")

    consumption_client = WatticsConsumptionClient(API_TOKEN)

    all_consumption_data = consumption_client.get_consumption_for_all_meters(
        meter_ids=meter_ids,
        start_year=START_YEAR,
        start_month=START_MONTH,
        end_year=END_YEAR,
        end_month=END_MONTH
    )

    consumption_df = consumption_client.to_dataframe(all_consumption_data)
    consumption_client.save_to_csv(
        consumption_df,
        filename=str(CONSUMPTION_FILE)
    )

    return consumption_df


def fetch_cost_data(meter_ids):
    print("\nFetching cost data for target meters...")

    cost_client = WatticsCostClient(API_TOKEN)

    all_cost_data = cost_client.get_all_meters_cost(
        meter_ids=meter_ids,
        start_year=START_YEAR,
        start_month=START_MONTH,
        end_year=END_YEAR,
        end_month=END_MONTH
    )

    cost_df = cost_client.to_dataframe(all_cost_data)
    cost_client.save(
        cost_df,
        filename=str(COST_FILE)
    )

    return cost_df


# =========================
# Merge data
# =========================

def merge_data(metadata):
    print("\nMerging data...")

    merger = DataMerger(
        cost_path=str(COST_FILE),
        consumption_path=str(CONSUMPTION_FILE),
        meter_metadata=metadata
    )

    df = merger.run()
    merger.save(str(MERGED_FILE))

    print(df.head())

    return df


# =========================
# Build KPIs
# =========================

def build_kpis():
    print("\nBuilding KPIs...")

    kpi_builder = KPIBuilder(
        merged_path=str(MERGED_FILE)
    )

    weekly = kpi_builder.run()
    kpi_builder.save(str(WEEKLY_KPIS_FILE))
    weekly.to_csv(str(LEGACY_WEEKLY_KPIS_FILE), index=False)

    print(weekly.head())

    return weekly

#detect anomalies:
def detect_anomalies():
    print("\nDetecting anomalies...")

    detector = AnomalyDetector(
        dataset_path=str(WEEKLY_KPIS_FILE),
        z_threshold=2.0
    )

    df_with_anomalies = detector.run()
    anomalies = detector.get_anomalies()

    df_with_anomalies.to_csv(DATASET_WITH_ANOMALIES_FILE, index=False)
    anomalies.to_csv(ANOMALIES_FILE, index=False)

    print(f"Total anomalies found: {len(anomalies)}")
    print(anomalies[["site_name", "week_start", "weekly_total_consumption", "wow_change_percent", "anomaly_reason"]].head())

    return df_with_anomalies, anomalies

#forecasting:
'''''
def forecast_next_week():
    print("\nForecasting next-week consumption...")

    forecaster = SiteForecaster(
        dataset_path=str(WEEKLY_KPIS_FILE),
        target_col="weekly_total_consumption",
        min_weeks=6,
        model_type="linear"
    )

    forecasts = forecaster.run()
    forecasts.to_csv(FORECASTS_FILE, index=False)

    print(f"Saved forecasts to: {FORECASTS_FILE}")
    print(forecasts.head())

    return forecasts'''

def forecast_next_week():
    print("\nForecasting next-week consumption...")

    forecaster = SiteForecaster(
        dataset_path=str(WEEKLY_KPIS_FILE),
        target_col="weekly_total_consumption",
        min_weeks=10,
        test_size=12
    )

    forecasts = forecaster.run()
    forecasts.to_csv(FORECASTS_FILE, index=False)

    print(f"Saved forecasts to: {FORECASTS_FILE}")
    print(forecasts)

    return forecasts
# evaluate forecasts:

def evaluate_forecasts():
    print("\nEvaluating forecast model...")

    evaluator = ForecastEvaluator(
        dataset_path=str(WEEKLY_KPIS_FILE),
        target_col="weekly_total_consumption",
        test_size=15
    )

    evaluation = evaluator.run()
    evaluation.to_csv(FORECAST_EVALUATION_FILE, index=False)

    print(f"Saved forecast evaluation to: {FORECAST_EVALUATION_FILE}")
    print(evaluation)

    return evaluation

#-----------------
#summary generation:
#------------------
def generate_insight_report():
    print("\nGenerating insight report with OpenAI...")

    generator = InsightReportGenerator(
        dataset_path=str(WEEKLY_KPIS_FILE),
        anomalies_path=str(ANOMALIES_FILE),
        forecasts_path=str(FORECASTS_FILE),
        output_path=str(SUMMARY_REPORT_FILE),
        model="gpt-4.1-mini"
    )

    report = generator.run()

    print(f"Saved summary report to: {SUMMARY_REPORT_FILE}")
    print(report)

    return report
#------------------
# visualization:
#------------------



#-------------------
#email report:
#-------------------
def send_email_report():
    print("\nSending email report...")

    if GMAIL_SENDER_EMAIL is None:
        raise ValueError("GMAIL_SENDER_EMAIL is not set.")

    if GMAIL_APP_PASSWORD is None:
        raise ValueError("GMAIL_APP_PASSWORD is not set.")

    if RECEIVER_EMAIL is None:
        raise ValueError("RECEIVER_EMAIL is not set.")

    email_body = """
Dear Sir/Madam,

I hope you are doing well.

Please find attached the Weekly Energy Intelligence Report. The report includes:

• Weekly KPIs and site-level performance
• Detected anomalies and unusual patterns
• Forecasts for next week’s consumption
• Model evaluation and performance comparison
• An interactive dashboard for detailed exploration

Kindly review the attached files for insights and recommendations.

Best regards,
Hasan Abbani
"""

    email_sender = EmailReportSender(
        sender_email=GMAIL_SENDER_EMAIL,
        app_password=GMAIL_APP_PASSWORD
    )

    email_sender.send_report(
        receiver_email=RECEIVER_EMAIL,
        subject="Weekly Energy Intelligence Report",
        body=email_body,
        attachment_paths=[
            str(WEEKLY_KPIS_FILE),
            str(ANOMALIES_FILE),
            str(FORECASTS_FILE),

            str(SUMMARY_REPORT_FILE),
            str(HTML_DASHBOARD_FILE)
        ]
    )
def generate_html_dashboard():
    print("\nGenerating interactive HTML dashboard...")

    dashboard = HTMLDashboardGenerator(
        dataset_path=str(WEEKLY_KPIS_FILE),
        anomalies_path=str(ANOMALIES_FILE),
        forecasts_path=str(FORECASTS_FILE),
        evaluation_path=str(FORECAST_EVALUATION_FILE),
        output_path=str(HTML_DASHBOARD_FILE)
    )

    dashboard.run()

    print(f"Saved dashboard to: {HTML_DASHBOARD_FILE}")

    return HTML_DASHBOARD_FILE

# =========================
# MAIN
# =========================

def main():
    print("\n=== PIPELINE STARTED ===")

    validate_environment()

    organizations = get_target_organizations()

    meter_ids, metadata = collect_meter_metadata(organizations)

    print(f"\nTotal meters collected: {len(meter_ids)}")

    # Regenerate source CSVs for all target organizations before merging
    #uncomment in order to fetch fresh data from the API, otherwise it will use the existing CSV files in the directory:
    
    #fetch_consumption_data(meter_ids)
    #fetch_cost_data(meter_ids)

    merge_data(metadata)
    build_kpis()

    # =========================
    # Detect anomalies
    # =========================
    detect_anomalies()

    #forecasting:
    forecast_next_week()
    
    #evaluating forecasts:
    evaluate_forecasts()
    
    #summary generation:
    generate_insight_report()
    
    #email and visuals
    
    #generate_chart() #this gives the .png plot
    generate_html_dashboard()

    send_email_report()
    
    generate_html_dashboard()

    # =========================
    # Rank sites
    # =========================
    
    print("\nRanking sites...")

    ranking = SiteRanking(str(WEEKLY_KPIS_FILE))
    ranked_df = ranking.run()

    best, worst = ranking.get_best_worst_latest_week()

    print("\nBest site by cost efficiency:")
    print(best[["site_name", "cost_per_kwh", "rank_efficiency"]])

    latest_week = ranked_df["week_start"].max()
    latest = ranked_df[ranked_df["week_start"] == latest_week]

    print("\nHighest consumption sites:")
    print(
        latest.sort_values("rank_consumption")
        [["site_name", "weekly_total_consumption", "rank_consumption"]]
        .head(3)
    )

    print("\nLargest week-over-week increases:")
    print(
        latest.sort_values("rank_wow_increase")
        [["site_name", "wow_change_percent", "rank_wow_increase"]]
        .head(3)
    )

    # Optional: save ranked dataset
    ranked_df.to_csv(BASE_DIR / "dataset_ranked.csv", index=False) # Same as dataset.csv but with additional ranking columns
    
    
    
    print("\n=== DATASET READY ===")


if __name__ == "__main__":
    main()
