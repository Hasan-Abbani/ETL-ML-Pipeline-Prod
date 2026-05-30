import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.ensemble import RandomForestRegressor

class ForecastEvaluator:
    def __init__(
        self,
        dataset_path,
        target_col="weekly_total_consumption",
        test_size=4
    ):
        self.dataset_path = dataset_path
        self.target_col = target_col
        self.test_size = test_size
        self.df = None
        self.results = None

    def load_data(self):
        self.df = pd.read_csv(self.dataset_path)
        self.df["week_start"] = pd.to_datetime(self.df["week_start"])
        self.df = self.df.sort_values(["site_id", "week_start"])

    def create_lag_features(self, site_df):
        site_df = site_df.copy()

        site_df["lag_1"] = site_df[self.target_col].shift(1)
        site_df["lag_2"] = site_df[self.target_col].shift(2)
        site_df["lag_3"] = site_df[self.target_col].shift(3)
        site_df["lag_4"] = site_df[self.target_col].shift(4)
        site_df["target_next_week"] = site_df[self.target_col].shift(-1)

        return site_df.dropna(
            subset=["lag_1", "lag_2", "lag_3","lag_4", "target_next_week"]
        )

    def safe_mape(self, y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        mask = y_true != 0

        if mask.sum() == 0:
            return np.nan

        return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    def evaluate_site(self, site_df):
        site_df = site_df.sort_values("week_start").copy()

        organization_name = site_df["organization_name"].iloc[0]
        site_id = site_df["site_id"].iloc[0]
        site_name = site_df["site_name"].iloc[0]

        model_df = self.create_lag_features(site_df)

        if len(model_df) <= self.test_size:
            return {
                "organization_name": organization_name,
                "site_id": site_id,
                "site_name": site_name,
                "test_size": self.test_size,
                "training_rows": 0,
                "model_mae": np.nan,
                "model_mape_percent": np.nan,
                "naive_mae": np.nan,
                "naive_mape_percent": np.nan,
                "mean_mae": np.nan,
                "mean_mape_percent": np.nan,
                "model_vs_naive": np.nan,
                "model_vs_mean": np.nan,
                "note": "Not enough data for time-based evaluation"
            }

        features = ["lag_1", "lag_2", "lag_3","lag_4"]

        X = model_df[features]
        y = model_df["target_next_week"]

        X_train = X.iloc[:-self.test_size]
        y_train = y.iloc[:-self.test_size]

        X_test = X.iloc[-self.test_size:]
        y_test = y.iloc[-self.test_size:]

        model = LinearRegression()
        '''''
        model = RandomForestRegressor(
            n_estimators=200,
            random_state=42
        )'''''
        model.fit(X_train, y_train)

        model_predictions = model.predict(X_test)

        # Model error
        model_mae = mean_absolute_error(y_test, model_predictions)
        model_mape_percent = self.safe_mape(y_test, model_predictions)

        # Naive baseline:
        # predict next week = previous week's consumption
        naive_predictions = X_test["lag_1"]
        naive_mae = mean_absolute_error(y_test, naive_predictions)
        naive_mape_percent = self.safe_mape(y_test, naive_predictions)

        # Mean baseline:
        # predict next week = average consumption from the training period
        mean_value = y_train.mean()
        mean_predictions = np.full(shape=len(y_test), fill_value=mean_value)

        mean_mae = mean_absolute_error(y_test, mean_predictions)
        mean_mape_percent = self.safe_mape(y_test, mean_predictions)

        model_vs_naive = (
            model_mae / naive_mae if naive_mae != 0 else np.nan
        )

        model_vs_mean = (
            model_mae / mean_mae if mean_mae != 0 else np.nan
        )

        return {
            "organization_name": organization_name,
            "site_id": site_id,
            "site_name": site_name,
            "test_size": self.test_size,
            "training_rows": len(X_train),

            "model_mae": model_mae,
            "model_mape_percent": model_mape_percent,

            "naive_mae": naive_mae,
            "naive_mape_percent": naive_mape_percent,

            "mean_mae": mean_mae,
            "mean_mape_percent": mean_mape_percent,

            "model_vs_naive": model_vs_naive,
            "model_vs_mean": model_vs_mean,

            "note": "Evaluation completed using last weeks as test set"
        }

    def run(self):
        self.load_data()

        results = []

        for _, site_df in self.df.groupby("site_id"):
            results.append(self.evaluate_site(site_df))

        self.results = pd.DataFrame(results)

        return self.results