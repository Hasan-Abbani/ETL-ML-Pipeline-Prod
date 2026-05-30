import pandas as pd
import numpy as np


class KPIBuilder:
    def __init__(self, merged_path):
        self.merged_path = merged_path
        self.df = None
        self.weekly = None

    def load_data(self):
        self.df = pd.read_csv(self.merged_path)
        self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")

        self.df["total_consumption"] = pd.to_numeric(
            self.df["total_consumption"], errors="coerce"
        )

        self.df["total_cost"] = pd.to_numeric(
            self.df["total_cost"], errors="coerce"
        )

        self.df = self.df.dropna(
            subset=[
                "date",
                "organization_id",
                "organization_name",
                "site_id",
                "site_name",
                "meter_id",
                "total_consumption",
                "total_cost"
            ]
        )

    def aggregate_weekly(self):
        self.df["week_start"] = (
            self.df["date"]
            .dt.to_period("W")
            .apply(lambda r: r.start_time)
        )

        self.weekly = (
            self.df
            .groupby(
                [
                    "organization_id",
                    "organization_name",
                    "site_id",
                    "site_name",
                    "week_start"
                ],
                as_index=False
            )
            .agg(
                weekly_total_consumption=("total_consumption", "sum"),
                weekly_avg_consumption=("total_consumption", "mean"),
                weekly_total_cost=("total_cost", "sum"),
                number_of_meters=("meter_id", "nunique")
            )
        )

    def compute_kpis(self):
        self.weekly["cost_per_kwh"] = np.where(
            self.weekly["weekly_total_consumption"] > 0,
            self.weekly["weekly_total_cost"] / self.weekly["weekly_total_consumption"],
            np.nan
        )

        self.weekly = self.weekly.sort_values(
            ["organization_id", "site_id", "week_start"]
        )

        self.weekly["wow_change_percent"] = (
            self.weekly
            .groupby(["organization_id", "site_id"])["weekly_total_consumption"]
            .pct_change() * 100
        )

    def remove_first_week_per_site(self):
        self.weekly = self.weekly.sort_values(
            ["organization_id", "site_id", "week_start"]
        )

        self.weekly["site_week_index"] = (
            self.weekly
            .groupby(["organization_id", "site_id"])
            .cumcount()
        )

        self.weekly = (
            self.weekly
            [self.weekly["site_week_index"] > 0]
            .drop(columns=["site_week_index"])
            .reset_index(drop=True)
        )

    def rank_sites(self):
        self.weekly["rank_highest_consumption"] = (
            self.weekly
            .groupby("week_start")["weekly_total_consumption"]
            .rank(ascending=False, method="dense")
        )

        self.weekly["rank_lowest_consumption"] = (
            self.weekly
            .groupby("week_start")["weekly_total_consumption"]
            .rank(ascending=True, method="dense")
        )

        self.weekly["rank_cost_efficiency"] = (
            self.weekly
            .groupby("week_start")["cost_per_kwh"]
            .rank(ascending=True, method="dense")
        )

        self.weekly["rank_largest_consumption_increase"] = (
            self.weekly
            .groupby("week_start")["wow_change_percent"]
            .rank(ascending=False, method="dense")
        )

    def get_best_worst(self):
        latest_week = self.weekly["week_start"].max()
        latest = self.weekly[self.weekly["week_start"] == latest_week]

        best = latest.loc[latest["cost_per_kwh"].idxmin()]
        worst = latest.loc[latest["cost_per_kwh"].idxmax()]

        return best, worst

    def save(self, output_path="weekly_kpis.csv"):
        self.weekly.to_csv(output_path, index=False)
        print(f"Saved weekly KPIs to {output_path}")

    def run(self):
        self.load_data()
        self.aggregate_weekly()
        self.compute_kpis()
        self.remove_first_week_per_site()
        self.rank_sites()

        self.weekly = self.weekly.reset_index(drop=True)

        return self.weekly