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


load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")


ORGANIZATION_NAMES = [
    "Food Corp.",
    "Best Resorts Hotels"
]

TARGET_SITE_IDS = [106, 107]

BASE_DIR = Path(__file__).resolve().parent

CONSUMPTION_FILE = BASE_DIR / "meter_consumption_data_False.csv"
COST_FILE = BASE_DIR / "cost_data.csv"
MERGED_FILE = BASE_DIR / "merged_consumption_costs.csv"
WEEKLY_KPIS_FILE = BASE_DIR / "dataset.csv"

START_YEAR = 2014
START_MONTH = 1
END_YEAR = 2026
END_MONTH = 12


def validate_environment():
    if API_TOKEN is None:
        raise ValueError("API_TOKEN is not set.")
    print("Environment validated.")


def get_target_organizations():
    org_client = WatticsOrganizationClient(API_TOKEN)

    organizations = []

    for org_name in ORGANIZATION_NAMES:
        org = org_client.get_organization_by_name(org_name)

        if org is None:
            print(f"Organization not found: {org_name}")
            continue

        organizations.append(org)

    if not organizations:
        raise ValueError("No target organizations found.")

    return organizations


def collect_meter_metadata(organizations):
    site_client = WatticsSiteClient(API_TOKEN)
    meter_client = WatticsMeterClient(API_TOKEN)

    all_meter_ids = []
    all_metadata = []

    for org in organizations:
        org_id = org["id"]
        org_name = org["name"]

        print(f"\nProcessing organization: {org_name} | ID: {org_id}")

        sites = site_client.get_sites_for_organization(org_id)

        target_sites = [
            site for site in sites
            if site.get("id") in TARGET_SITE_IDS
        ]

        if not target_sites:
            print(f"No selected sites found inside {org_name}.")
            continue

        for site in target_sites:
            site_id = site["id"]
            site_name = site["name"]

            print(f"\nUsing site: {site_name} | ID: {site_id} | Organization: {org_name}")

            electricity_meters = meter_client.get_electricity_meters_for_site(
                organization_id=org_id,
                site_id=site_id
            )

            for meter in electricity_meters:
                meter_id = meter["id"]

                all_meter_ids.append(meter_id)

                all_metadata.append({
                    "meter_id": meter_id,
                    "organization_id": org_id,
                    "organization_name": org_name,
                    "site_id": site_id,
                    "site_name": site_name
                })

    if len(all_meter_ids) == 0:
        raise ValueError("No electricity meters found for the selected organizations/sites.")

    return all_meter_ids, all_metadata


def fetch_consumption_data(meter_ids):
    print("\nFetching consumption data...")

    client = WatticsConsumptionClient(API_TOKEN)

    all_data = client.get_consumption_for_all_meters(
        meter_ids=meter_ids,
        start_year=START_YEAR,
        start_month=START_MONTH,
        end_year=END_YEAR,
        end_month=END_MONTH
    )

    df = client.to_dataframe(all_data)
    client.save_to_csv(df, filename=str(CONSUMPTION_FILE))

    return df


def fetch_cost_data(meter_ids):
    print("\nFetching cost data...")

    client = WatticsCostClient(API_TOKEN)

    all_data = client.get_all_meters_cost(
        meter_ids=meter_ids,
        start_year=START_YEAR,
        start_month=START_MONTH,
        end_year=END_YEAR,
        end_month=END_MONTH
    )

    df = client.to_dataframe(all_data)
    client.save(df, filename=str(COST_FILE))

    return df


def merge_data(metadata):
    print("\nMerging data...")

    merger = DataMerger(
        cost_path=str(COST_FILE),
        consumption_path=str(CONSUMPTION_FILE),
        meter_metadata=metadata
    )

    df = merger.run()
    merger.save(output_path=str(MERGED_FILE))

    return df


def build_kpis():
    print("\nBuilding final dataset...")

    kpi_builder = KPIBuilder(
        merged_path=str(MERGED_FILE)
    )

    df = kpi_builder.run()
    kpi_builder.save(output_path=str(WEEKLY_KPIS_FILE))

    return df


def main():
    print("\n=== FILTERED PIPELINE STARTED ===")

    validate_environment()

    organizations = get_target_organizations()

    print("\nSelected organizations:")
    for org in organizations:
        print(f"{org['name']} | ID: {org['id']}")

    meter_ids, metadata = collect_meter_metadata(organizations)

    print(f"\nTotal selected meters: {len(meter_ids)}")

    fetch_consumption_data(meter_ids)
    fetch_cost_data(meter_ids)

    merge_data(metadata)
    build_kpis()

    print("\n=== DATASET READY ===")
    print(f"Saved final dataset to: {WEEKLY_KPIS_FILE}")


if __name__ == "__main__":
    main()