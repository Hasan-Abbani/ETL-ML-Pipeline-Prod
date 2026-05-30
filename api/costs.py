import requests
import pandas as pd


class WatticsCostClient:

    def __init__(self, api_token):
        self.base_url = "https://api.wattics.com/api/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": api_token
        }

    def get_meter_cost(self, meter_id, month, year, detailed=True):
        url = f"{self.base_url}/meters/{meter_id}/costs"

        params = {
            "month": month,
            "year": year,
            "detailed": str(detailed).lower()
        }

        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            print(f"Error for meter {meter_id}, {month}/{year}")
            print(response.status_code, response.text)
            return None

        return response.json()

    def get_cost_over_time(
        self,
        meter_id,
        start_year,
        start_month,
        end_year,
        end_month
    ):
        results = []

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):

                if year == start_year and month < start_month:
                    continue

                if year == end_year and month > end_month:
                    continue

                print(f"Fetching cost for meter {meter_id}, {month}/{year}...")

                data = self.get_meter_cost(meter_id, month, year)

                if data is not None:
                    results.append({
                        "meter_id": meter_id,
                        "year": year,
                        "month": month,
                        "data": data
                    })

        return results

    def get_all_meters_cost(
        self,
        meter_ids,
        start_year,
        start_month,
        end_year,
        end_month
    ):
        all_results = []

        for meter_id in meter_ids:
            print(f"\nStarting cost extraction for meter {meter_id}...")

            meter_data = self.get_cost_over_time(
                meter_id=meter_id,
                start_year=start_year,
                start_month=start_month,
                end_year=end_year,
                end_month=end_month
            )

            all_results.extend(meter_data)

            print(f"Finished cost extraction for meter {meter_id}.")

        return all_results

    def to_dataframe(self, all_data):
        rows = []

        for item in all_data:
            meter_id = item["meter_id"]
            year = item["year"]
            month = item["month"]
            data = item["data"]

            if isinstance(data, list):
                for record in data:
                    record["meter_id"] = meter_id
                    record["year"] = year
                    record["month"] = month
                    rows.append(record)

            elif isinstance(data, dict):
                data["meter_id"] = meter_id
                data["year"] = year
                data["month"] = month
                rows.append(data)

        df = pd.DataFrame(rows)

        print(f"Cost dataframe created with shape: {df.shape}")

        return df

    def save(self, df, filename="cost_data.csv"):
        df.to_csv(filename, index=False)
        print(f"Saved cost data to {filename}")