import requests
import pandas as pd


class WatticsConsumptionClient:
    def __init__(self, api_token):
        self.base_url = "https://api.wattics.com/api/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": api_token
        }

    def get_meter_consumption(self, meter_id, month, year, detailed=True):
        url = f"{self.base_url}/meters/{meter_id}/consumptions"

        params = {
            "month": month,
            "year": year,
            "detailed": str(detailed).lower()
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            print(f"Error for meter {meter_id}, {month}/{year}: {response.status_code}")
            print(response.text)
            return None

        return response.json()

    def get_consumption_for_meter_over_dates(
        self,
        meter_id,
        start_year,
        start_month,
        end_year,
        end_month
    ):
        meter_data = []

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):

                if year == start_year and month < start_month:
                    continue

                if year == end_year and month > end_month:
                    continue

                print(f"Fetching consumption for meter {meter_id}, {month}/{year}...")

                data = self.get_meter_consumption(
                    meter_id=meter_id,
                    month=month,
                    year=year
                )

                if data is not None:
                    meter_data.append({
                        "meter_id": meter_id,
                        "month": month,
                        "year": year,
                        "data": data
                    })

        return meter_data

    def get_consumption_for_all_meters(
        self,
        meter_ids,
        start_year,
        start_month,
        end_year,
        end_month
    ):
        all_data = []

        for meter_id in meter_ids:
            print(f"\nStarting consumption extraction for meter {meter_id}...")

            data = self.get_consumption_for_meter_over_dates(
                meter_id=meter_id,
                start_year=start_year,
                start_month=start_month,
                end_year=end_year,
                end_month=end_month
            )

            all_data.extend(data)

            print(f"Finished consumption extraction for meter {meter_id}.")

        return all_data

    def to_dataframe(self, all_data):
        rows = []

        for item in all_data:
            meter_id = item["meter_id"]
            month = item["month"]
            year = item["year"]
            data = item["data"]

            if isinstance(data, list):
                for record in data:
                    record["meter_id"] = meter_id
                    record["month"] = month
                    record["year"] = year
                    rows.append(record)

            elif isinstance(data, dict):
                data["meter_id"] = meter_id
                data["month"] = month
                data["year"] = year
                rows.append(data)

        df = pd.DataFrame(rows)

        print(f"Consumption dataframe created with shape: {df.shape}")

        return df

    def save_to_csv(self, df, filename="meter_consumption.csv"):
        df.to_csv(filename, index=False)
        print(f"Saved consumption data to {filename}")