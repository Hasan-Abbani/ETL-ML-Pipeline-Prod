import pandas as pd
import numpy as np


class AnomalyDetector:
    def __init__(self, dataset_path, z_threshold=2.0):
        self.dataset_path = dataset_path
        self.z_threshold = z_threshold
        self.df = None

    def load_data(self):
        self.df = pd.read_csv(self.dataset_path)
        self.df["week_start"] = pd.to_datetime(self.df["week_start"])

    def detect_anomalies(self):
        self.df = self.df.sort_values(["site_id", "week_start"])

        self.df["site_mean_consumption"] = (
            self.df.groupby("site_id")["weekly_total_consumption"]
            .transform("mean")
        )

        self.df["site_std_consumption"] = (
            self.df.groupby("site_id")["weekly_total_consumption"]
            .transform("std")
        )

        self.df["consumption_z_score"] = (
            (self.df["weekly_total_consumption"] - self.df["site_mean_consumption"])
            / self.df["site_std_consumption"]
        )

        self.df["is_consumption_anomaly"] = (
            self.df["consumption_z_score"].abs() >= self.z_threshold
        )

        self.df["is_wow_anomaly"] = (
            self.df["wow_change_percent"].abs() >= 30
        )

        self.df["is_anomaly"] = (
            self.df["is_consumption_anomaly"] | self.df["is_wow_anomaly"]
        )

        self.df["anomaly_reason"] = np.select(
            [
                self.df["is_consumption_anomaly"] & self.df["is_wow_anomaly"],
                self.df["is_consumption_anomaly"],
                self.df["is_wow_anomaly"]
            ],
            [
                "Unusual consumption level and large week-over-week change",
                "Unusual consumption level compared to site history",
                "Large week-over-week change"
            ],
            default="Normal"
        )

    def get_anomalies(self):
        return self.df[self.df["is_anomaly"]].copy()

    def run(self):
        self.load_data()
        self.detect_anomalies()
        return self.df