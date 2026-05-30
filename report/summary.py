import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


class LLMSummaryReportGenerator:
    def __init__(self, kpi_path, output_path="summary_report.txt"):
        load_dotenv()

        self.kpi_path = kpi_path
        self.output_path = output_path
        self.client = OpenAI(api_key=os.getenv("API_KEY"))

    def load_data(self):
        return pd.read_csv(self.kpi_path)

    def build_insights(self, df):
        best_row = df.loc[df["weekly_total_consumption"].idxmin()]
        worst_row = df.loc[df["weekly_total_consumption"].idxmax()]

        avg_consumption = df["weekly_total_consumption"].mean()
        avg_cost = df["weekly_total_cost"].mean()
        avg_cost_per_kwh = df["cost_per_kwh"].mean()

        insights = f"""
Dataset summary:
- Number of rows: {len(df)}
- Number of sites: {df["site_name"].nunique()}
- Number of meters: {df["meter_id"].nunique()}
- Date range: {df["week_start"].min()} to {df["week_start"].max()}

Average KPIs:
- Average weekly consumption: {avg_consumption:.2f} kWh
- Average weekly cost: {avg_cost:.2f}
- Average cost per kWh: {avg_cost_per_kwh:.4f}

Best performing meter/week:
- Site: {best_row["site_name"]}
- Meter ID: {best_row["meter_id"]}
- Week: {best_row["week_start"]}
- Consumption: {best_row["weekly_total_consumption"]:.2f} kWh
- Cost: {best_row["weekly_total_cost"]:.2f}

Worst performing meter/week:
- Site: {worst_row["site_name"]}
- Meter ID: {worst_row["meter_id"]}
- Week: {worst_row["week_start"]}
- Consumption: {worst_row["weekly_total_consumption"]:.2f} kWh
- Cost: {worst_row["weekly_total_cost"]:.2f}
"""
        return insights

    def generate_llm_summary(self, insights):
        prompt = f"""
You are an energy data analyst.

Write a clear, professional summary report based on the following KPI results.

The report should include:
1. A short overview
2. Key consumption insights
3. Cost insights
4. Best and worst performing meter/week
5. Practical recommendations

Keep it concise and suitable for a business stakeholder.

KPI insights:
{insights}
"""

        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        return response.output_text

    def save_summary(self, summary):
        with open(self.output_path, "w", encoding="utf-8") as file:
            file.write(summary)

        print(f"Summary report saved to {self.output_path}")

    def run(self):
        df = self.load_data()
        insights = self.build_insights(df)
        summary = self.generate_llm_summary(insights)
        self.save_summary(summary)

        return summary



