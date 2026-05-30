from api.consumption import WatticsConsumptionClient
from api.costs import WatticsCostClient
import os
from dotenv import load_dotenv

load_dotenv()


def find_oldest_year_month(client, meter_id):
    for year in range(2010, 2030):
        for month in range(1, 13):
            data = client.get_meter_consumption(meter_id, month, year)

            if data:
                return year, month


def find_oldest_year_month_cost(client, meter_id):
    for year in range(2010, 2030):
        for month in range(1, 13):
            data = client.get_meter_cost(meter_id, month, year)

            if data:
                return year, month


# Initialize clients
client = WatticsConsumptionClient(os.getenv("API_TOKEN"))
client1 = WatticsCostClient(os.getenv("API_TOKEN"))

# List of meters you care about
meter_ids = [751, 749, 750, 110516]  


print("\n--- Consumption Oldest Dates ---")
for meter_id in meter_ids:
    result = find_oldest_year_month(client, meter_id)
    if result:
        year, month = result
        print(f"Meter {meter_id}: {month}/{year}")
    else:
        print(f"Meter {meter_id}: No data found")


print("\n--- Cost Oldest Dates ---")
for meter_id in meter_ids:
    result = find_oldest_year_month_cost(client1, meter_id)
    if result:
        year, month = result
        print(f"Meter {meter_id}: {month}/{year}")
    else:
        print(f"Meter {meter_id}: No data found")