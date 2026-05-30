import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


class SiteForecaster:
    def __init__(
        self,
        dataset_path,
        target_col="weekly_total_consumption",
        min_weeks=10,
        test_size=12
    ):
        self.dataset_path = dataset_path
        self.target_col = target_col
        self.min_weeks = min_weeks
        self.test_size = test_size
        self.df = None
        self.forecasts = None

    def load_data(self):
        self.df = pd.read_csv(self.dataset_path)
        self.df["week_start"] = pd.to_datetime(self.df["week_start"])
        self.df = self.df.sort_values(["site_id", "week_start"])

    def create_lag_features(self, site_df):
        site_df = site_df.copy()

        site_df["lag_1"] = site_df[self.target_col].shift(1)
        site_df["lag_2"] = site_df[self.target_col].shift(2)
        site_df["lag_3"] = site_df[self.target_col].shift(3)
        site_df["target_next_week"] = site_df[self.target_col].shift(-1)

        return site_df.dropna(
            subset=["lag_1", "lag_2", "lag_3", "target_next_week"]
        )

    def train_and_evaluate_models(self, model_df):
        features = ["lag_1", "lag_2", "lag_3"]

        X = model_df[features]
        y = model_df["target_next_week"]

        X_train = X.iloc[:-self.test_size]
        y_train = y.iloc[:-self.test_size]

        X_test = X.iloc[-self.test_size:]
        y_test = y.iloc[-self.test_size:]

        results = {}

        linear = LinearRegression()
        linear.fit(X_train, y_train)
        linear_pred = linear.predict(X_test)
        results["linear"] = {
            "model": linear,
            "mae": mean_absolute_error(y_test, linear_pred)
        }

        rf = RandomForestRegressor(
            n_estimators=200,
            random_state=42
        )
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        results["random_forest"] = {
            "model": rf,
            "mae": mean_absolute_error(y_test, rf_pred)
        }

        naive_pred = X_test["lag_1"]
        results["naive"] = {
            "model": None,
            "mae": mean_absolute_error(y_test, naive_pred)
        }

        best_model_name = min(results, key=lambda name: results[name]["mae"])

        return best_model_name, results

    def forecast_site(self, site_df):
        site_df = site_df.sort_values("week_start").copy()

        organization_name = site_df["organization_name"].iloc[0]
        site_id = site_df["site_id"].iloc[0]
        site_name = site_df["site_name"].iloc[0]

        latest_week = site_df["week_start"].max()
        forecast_week = latest_week + pd.Timedelta(days=7)

        if len(site_df) < self.min_weeks:
            return {
                "organization_name": organization_name,
                "site_id": site_id,
                "site_name": site_name,
                "latest_week": latest_week,
                "forecast_week": forecast_week,
                "predicted_next_week_consumption": np.nan,
                "selected_model": None,
                "linear_mae": np.nan,
                "random_forest_mae": np.nan,
                "naive_mae": np.nan,
                "selected_model_mae": np.nan,
                "confidence_lower": np.nan,
                "confidence_upper": np.nan,
                "note": "Not enough weekly data"
            }

        model_df = self.create_lag_features(site_df)

        if len(model_df) <= self.test_size:
            return {
                "organization_name": organization_name,
                "site_id": site_id,
                "site_name": site_name,
                "latest_week": latest_week,
                "forecast_week": forecast_week,
                "predicted_next_week_consumption": np.nan,
                "selected_model": None,
                "linear_mae": np.nan,
                "random_forest_mae": np.nan,
                "naive_mae": np.nan,
                "selected_model_mae": np.nan,
                "confidence_lower": np.nan,
                "confidence_upper": np.nan,
                "note": "Not enough rows for model selection"
            }

        best_model_name, results = self.train_and_evaluate_models(model_df)

        latest_values = site_df[self.target_col].tail(3).values

        X_next = pd.DataFrame(
            [[latest_values[-1], latest_values[-2], latest_values[-3]]],
            columns=["lag_1", "lag_2", "lag_3"]
        )

        if best_model_name == "naive":
            prediction = latest_values[-1]
        else:
            best_model = results[best_model_name]["model"]

            # Retrain selected model on ALL available lagged data before forecasting
            X_all = model_df[["lag_1", "lag_2", "lag_3"]]
            y_all = model_df["target_next_week"]
            best_model.fit(X_all, y_all)

            prediction = best_model.predict(X_next)[0]

        selected_mae = results[best_model_name]["mae"]

        return {
            "organization_name": organization_name,
            "site_id": site_id,
            "site_name": site_name,
            "latest_week": latest_week,
            "forecast_week": forecast_week,
            "predicted_next_week_consumption": prediction,
            "selected_model": best_model_name,
            "linear_mae": results["linear"]["mae"],
            "random_forest_mae": results["random_forest"]["mae"],
            "naive_mae": results["naive"]["mae"],
            "selected_model_mae": selected_mae,
            "confidence_lower": prediction - selected_mae,
            "confidence_upper": prediction + selected_mae,
            "note": "Forecast generated using best validation model"
        }

    def run(self):
        self.load_data()

        results = []

        for _, site_df in self.df.groupby("site_id"):
            results.append(self.forecast_site(site_df))

        self.forecasts = pd.DataFrame(results)

        return self.forecasts