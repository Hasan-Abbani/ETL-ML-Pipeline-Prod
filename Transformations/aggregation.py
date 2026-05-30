import pandas as pd


class DataMerger:
    def __init__(self, cost_path, consumption_path, meter_metadata=None):
        self.cost_path = cost_path
        self.consumption_path = consumption_path
        self.meter_metadata = meter_metadata

        self.costs = None
        self.consumption = None
        self.merged = None
        self.final = None

    def load_data(self):
        self.costs = pd.read_csv(self.cost_path)
        self.consumption = pd.read_csv(self.consumption_path)

    def clean_data(self):
        self.costs["date"] = pd.to_datetime(self.costs["date"], errors="coerce")
        self.consumption["date"] = pd.to_datetime(
            self.consumption["date"], errors="coerce"
        )

        self.consumption["total_consumption"] = (
            self.consumption["total_consumption"]
            .astype(str)
            .str.replace(" kWh", "", regex=False)
            .str.replace(",", "", regex=False)
        )

        self.consumption["total_consumption"] = pd.to_numeric(
            self.consumption["total_consumption"], errors="coerce"
        )

        self.costs["total_cost"] = pd.to_numeric(
            self.costs["total_cost"], errors="coerce"
        )

        self.costs = self.costs.dropna(subset=["date", "meter_id", "total_cost"])
        self.consumption = self.consumption.dropna(
            subset=["date", "meter_id", "total_consumption"]
        )

    def merge_data(self):
        self.merged = pd.merge(
            self.consumption,   # LEFT table: keep all consumption rows
            self.costs,         # RIGHT table: attach cost if available
            on=["date", "meter_id"],
            how="inner",  # Only keep rows where both consumption and cost exist    #change to left to keep all consumption records, even if cost is missing
            suffixes=("_consumption", "_cost")
        )

        self.merged["total_cost"] = self.merged["total_cost"].fillna(0)

    def add_meter_metadata(self):
        if self.meter_metadata is None:
            self.final["organization_id"] = "Unknown"
            self.final["organization_name"] = "Unknown"
            self.final["site_id"] = "Unknown"
            self.final["site_name"] = "Unknown"
            return

        metadata_df = pd.DataFrame(self.meter_metadata)

        required_columns = [
            "meter_id",
            "organization_id",
            "organization_name",
            "site_id",
            "site_name"
        ]

        missing_columns = [
            col for col in required_columns if col not in metadata_df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"meter_metadata is missing required columns: {missing_columns}"
            )

        metadata_df = metadata_df[required_columns].drop_duplicates(
            subset=["meter_id"]
        )

        self.final = pd.merge(
            self.final,
            metadata_df,
            on="meter_id",
            how="left"
        )

    def finalize(self):
        self.final = self.merged.copy()

        self.final["month"] = self.final["date"].dt.month
        self.final["year"] = self.final["date"].dt.year

        self.final = self.final[
            [
                "date",
                "meter_id",
                "total_consumption",
                "total_cost",
                "month",
                "year"
            ]
        ]

        self.add_meter_metadata()

        self.final = self.final[
            [
                "organization_id",
                "organization_name",
                "site_id",
                "site_name",
                "meter_id",
                "date",
                "month",
                "year",
                "total_consumption",
                "total_cost"
            ]
        ]

        self.final = self.final.sort_values(
            by=["organization_name", "site_name", "meter_id", "date"]
        )

    def save(self, output_path="merged_consumption_costs.csv"):
        self.final.to_csv(output_path, index=False)
        print(f"Saved merged data to {output_path}")

    def run(self):
        self.load_data()
        self.clean_data()
        self.merge_data()
        self.finalize()
        return self.final