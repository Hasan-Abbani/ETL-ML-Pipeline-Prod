import os
import pandas as pd
from openai import OpenAI


class InsightReportGenerator:
    def __init__(
        self,
        dataset_path,
        anomalies_path,
        forecasts_path,
        output_path,
        model="gpt-4.1-mini"
    ):
        self.dataset_path = dataset_path
        self.anomalies_path = anomalies_path
        self.forecasts_path = forecasts_path
        self.output_path = output_path
        self.model = model

        self.client = OpenAI(api_key=os.getenv("API_KEY"))

    def load_data(self):
        dataset = pd.read_csv(self.dataset_path)
        anomalies = pd.read_csv(self.anomalies_path)
        forecasts = pd.read_csv(self.forecasts_path)

        return dataset, anomalies, forecasts

    def build_prompt(self, dataset, anomalies, forecasts):
        latest_week = dataset["week_start"].max()
        latest_data = dataset[dataset["week_start"] == latest_week]

        return f"""
You are an energy data analyst preparing a weekly management report.

Write a polished, human-readable report including:

1. Current trends and anomalies
2. Predicted next-week performance per site
3. Suggested actions or focus areas

Use the data below.

Latest week:
{latest_week}

Latest KPI data:
{latest_data.to_string(index=False)}

Detected anomalies:
{anomalies.to_string(index=False)}

Forecasts:
{forecasts.to_string(index=False)}

Keep the report concise, professional, and action-oriented.
"""

    def generate_report(self):
        dataset, anomalies, forecasts = self.load_data()
        prompt = self.build_prompt(dataset, anomalies, forecasts)

        response = self.client.responses.create(
            model=self.model,
            input=prompt
        )

        report_text = response.output_text

        with open(self.output_path, "w", encoding="utf-8") as file:
            file.write(report_text)

        return report_text

    def run(self):
        return self.generate_report()