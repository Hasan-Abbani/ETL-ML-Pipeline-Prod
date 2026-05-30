import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class HTMLDashboardGenerator:
    def __init__(
        self,
        dataset_path,
        anomalies_path,
        forecasts_path,
        evaluation_path,
        output_path
    ):
        self.dataset_path = dataset_path
        self.anomalies_path = anomalies_path
        self.forecasts_path = forecasts_path
        self.evaluation_path = evaluation_path
        self.output_path = output_path

        self.primary_color = "#800020"   # burgundy
        self.light_bg = "#ffffff"

    def load_data(self):
        dataset = pd.read_csv(self.dataset_path)
        anomalies = pd.read_csv(self.anomalies_path)
        forecasts = pd.read_csv(self.forecasts_path)
        evaluation = pd.read_csv(self.evaluation_path)

        dataset["week_start"] = pd.to_datetime(dataset["week_start"])
        anomalies["week_start"] = pd.to_datetime(anomalies["week_start"], errors="coerce")
        forecasts["forecast_week"] = pd.to_datetime(forecasts["forecast_week"], errors="coerce")

        return dataset, anomalies, forecasts, evaluation

    def style_fig(self, fig, title):
        fig.update_layout(
            title=title,
            template="plotly_white",
            paper_bgcolor=self.light_bg,
            plot_bgcolor=self.light_bg,
            title_font=dict(size=20, color=self.primary_color),
            legend_title_text="",
            margin=dict(l=40, r=40, t=70, b=40),
            hovermode="x unified"
        )
        return fig

    def create_consumption_overview_chart(self, dataset, anomalies, forecasts):
        fig = px.line(
            dataset,
            x="week_start",
            y="weekly_total_consumption",
            color="site_name",
            markers=True,
            hover_data=[
                "organization_name",
                "weekly_total_cost",
                "cost_per_kwh",
                "wow_change_percent",
                "number_of_meters"
            ]
        )

        if len(anomalies) > 0:
            fig.add_trace(
                go.Scatter(
                    x=anomalies["week_start"],
                    y=anomalies["weekly_total_consumption"],
                    mode="markers",
                    marker=dict(size=10, symbol="x", color=self.primary_color),
                    name="Detected Anomalies",
                    text=anomalies["anomaly_reason"],
                    hovertemplate="Week: %{x}<br>Consumption: %{y}<br>Reason: %{text}<extra></extra>"
                )
            )

        for _, row in forecasts.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row["forecast_week"]],
                    y=[row["predicted_next_week_consumption"]],
                    mode="markers",
                    marker=dict(size=12, symbol="diamond", color=self.primary_color),
                    name=f"Forecast - {row['site_name']}",
                    hovertemplate=(
                        f"Site: {row['site_name']}<br>"
                        f"Selected model: {row.get('selected_model', 'N/A')}<br>"
                        "Forecast: %{y}<br>"
                        "Week: %{x}<extra></extra>"
                    )
                )
            )

        return self.style_fig(
            fig,
            "Weekly Consumption Trends with Anomalies and Forecasts"
        )

    def create_cost_efficiency_chart(self, dataset):
        latest_week = dataset["week_start"].max()
        latest = dataset[dataset["week_start"] == latest_week]

        fig = px.bar(
            latest,
            x="site_name",
            y="cost_per_kwh",
            color="site_name",
            hover_data=["weekly_total_consumption", "weekly_total_cost"]
        )
        return self.style_fig(fig, f"Cost Efficiency by Site — Latest Week ({latest_week.date()})")

    def create_wow_chart(self, dataset):
        dataset = dataset[dataset["week_start"] >= "2025-01-01"]

        fig = px.line(
            dataset,
            x="week_start",
            y="wow_change_percent",
            color="site_name",
            markers=True,
            hover_data=["weekly_total_consumption"]
        )

        fig.add_hline(y=30, line_dash="dash", line_color=self.primary_color)
        fig.add_hline(y=-30, line_dash="dash", line_color=self.primary_color)

        return self.style_fig(fig, "Week-over-Week Consumption Change (%) as of 2025")



    
    def create_smoothed_trend(self, dataset):
        dataset = dataset.sort_values(["site_name", "week_start"])

        dataset["rolling_consumption"] = (
            dataset
            .groupby("site_name")["weekly_total_consumption"]
            .transform(lambda x: x.rolling(3).mean())
        )

        fig = px.line(
            dataset,
            x="week_start",
            y="rolling_consumption",
            color="site_name",
            title="Smoothed Consumption Trend (3-week moving average)"
        )

        return self.style_fig(fig, "Smoothed Consumption Trend")
    
    def create_ranking_evolution(self, dataset):
        fig = px.line(
            dataset,
            x="week_start",
            y="rank_cost_efficiency",
            color="site_name",
            markers=True,
            title="Cost Efficiency Ranking Over Time"
        )

        fig.update_yaxes(autorange="reversed")

        return self.style_fig(fig, "Ranking Evolution (Lower is Better)")
    
    def create_forecast_vs_actual(self, dataset, forecasts):
        fig = px.line(
            dataset,
            x="week_start",
            y="weekly_total_consumption",
            color="site_name"
        )

        for _, row in forecasts.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row["forecast_week"]],
                    y=[row["predicted_next_week_consumption"]],
                    mode="markers",
                    marker=dict(size=10, color="black"),
                    name=f"Forecast - {row['site_name']}"
                )
            )

        return self.style_fig(fig, "Forecast vs Actual")


    def create_model_comparison_chart(self, evaluation):
        melted = evaluation.melt(
            id_vars=["site_name"],
            value_vars=["model_mae", "naive_mae", "mean_mae"],
            var_name="model",
            value_name="mae"
        )

        fig = px.bar(
            melted,
            x="site_name",
            y="mae",
            color="model",
            barmode="group",
            hover_data=["mae"]
        )

        return self.style_fig(fig, "Model Evaluation: MAE vs Baselines")
    
    def create_cost_trend(self, dataset):
        dataset = dataset.sort_values(["site_name", "week_start"])

        fig = px.line(
            dataset,
            x="week_start",
            y="cost_per_kwh",
            color="site_name",
            markers=False,
            hover_data={
                "cost_per_kwh": ":.4f",
                "weekly_total_cost": ":,.2f",
                "weekly_total_consumption": ":,.2f"
            },
            title="Cost per kWh Trend Over Time"
        )

        # Smooth trend (optional but recommended)
        dataset["rolling_cost"] = (
            dataset
            .groupby("site_name")["cost_per_kwh"]
            .transform(lambda x: x.rolling(4).mean())
        )


        fig.update_traces(line=dict(width=2))

        return self.style_fig(fig, "Cost per kWh Trend Over Time")

    def create_summary_cards(self, dataset, anomalies, forecasts, evaluation):
        latest_week = dataset["week_start"].max()
        latest = dataset[dataset["week_start"] == latest_week]

        total_consumption = latest["weekly_total_consumption"].sum()
        total_cost = latest["weekly_total_cost"].sum()
        anomaly_count = len(anomalies)
        avg_mape = evaluation["model_mape_percent"].mean()

        return f"""
        <div class="cards">
            <div class="card"><h3>Latest Week</h3><p>{latest_week.date()}</p></div>
            <div class="card"><h3>Total Consumption</h3><p>{total_consumption:,.2f}</p></div>
            <div class="card"><h3>Total Cost</h3><p>{total_cost:,.2f}</p></div>
            <div class="card"><h3>Anomalies</h3><p>{anomaly_count}</p></div>
            <div class="card"><h3>Avg Forecast MAPE</h3><p>{avg_mape:.2f}%</p></div>
        </div>
        """

    def build_html(self):
        dataset, anomalies, forecasts, evaluation = self.load_data()
        figures = [
            self.create_consumption_overview_chart(dataset, anomalies, forecasts),
   
            self.create_cost_efficiency_chart(dataset),

            self.create_wow_chart(dataset),

            self.create_cost_trend(dataset)
            
        ]

        charts_html = "\n".join(
            fig.to_html(full_html=False, include_plotlyjs="cdn")
            for fig in figures
        )

        cards_html = self.create_summary_cards(dataset, anomalies, forecasts, evaluation)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Weekly Energy Intelligence Dashboard</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #ffffff;
                    color: #222;
                    margin: 0;
                    padding: 0;
                }}

                header {{
                    background-color: {self.primary_color};
                    color: white;
                    padding: 28px 40px;
                }}

                header h1 {{
                    margin: 0;
                    font-size: 30px;
                }}

                header p {{
                    margin-top: 8px;
                    font-size: 15px;
                    opacity: 0.9;
                }}

                .container {{
                    padding: 30px 40px;
                }}

                .cards {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                    gap: 18px;
                    margin-bottom: 30px;
                }}

                .card {{
                    border: 1px solid #eee;
                    border-left: 6px solid {self.primary_color};
                    border-radius: 12px;
                    padding: 18px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                    background: white;
                }}

                .card h3 {{
                    margin: 0;
                    color: {self.primary_color};
                    font-size: 15px;
                }}

                .card p {{
                    margin: 10px 0 0 0;
                    font-size: 22px;
                    font-weight: bold;
                }}

                section {{
                    margin-bottom: 40px;
                }}

                .note {{
                    background-color: #faf7f8;
                    border-left: 5px solid {self.primary_color};
                    padding: 16px;
                    margin-bottom: 28px;
                    border-radius: 8px;
                    line-height: 1.5;
                }}
            </style>
        </head>

        <body>
            <header>
                <h1>Weekly Energy Intelligence Dashboard</h1>
                <p>Interactive dashboard covering KPIs, rankings, anomalies, forecasts, and model evaluation.</p>
            </header>

            <div class="container">
                {cards_html}

                <div class="note">
                    <strong>Interpretation note:</strong>
                    Forecasts are generated per site using the best validation model selected from linear regression,
                    random forest, and naive baseline. Anomalies are detected per site using consumption deviation and
                    week-over-week change.
                </div>

                <section>
                    {charts_html}
                </section>
            </div>
        </body>
        </html>
        """

        with open(self.output_path, "w", encoding="utf-8") as file:
            file.write(html)

        print(f"HTML dashboard saved to: {self.output_path}")

        return self.output_path

    def run(self):
        return self.build_html()