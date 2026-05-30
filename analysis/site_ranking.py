import pandas as pd



class SiteRanking:
    def __init__(self, dataset_path):
        self.dataset_path = dataset_path
        self.df = None

    def load_data(self):
        self.df = pd.read_csv(self.dataset_path)

    def rank_sites(self):
        # Rank by cost efficiency (lower is better)
        self.df["rank_efficiency"] = (
            self.df.groupby("week_start")["cost_per_kwh"]
            .rank(ascending=True)
        )

        # Rank by consumption (higher demand)
        self.df["rank_consumption"] = (
            self.df.groupby("week_start")["weekly_total_consumption"]
            .rank(ascending=False)
        )

        # Rank by WoW increase (higher = suspicious)
        self.df["rank_wow_increase"] = (
            self.df.groupby("week_start")["wow_change_percent"]
            .rank(ascending=False)
        )

    def get_best_worst_latest_week(self):
        latest_week = self.df["week_start"].max()
        latest = self.df[self.df["week_start"] == latest_week]

        best = latest.loc[latest["cost_per_kwh"].idxmin()]
        worst = latest.loc[latest["cost_per_kwh"].idxmax()]

        return best, worst

    def run(self):
        self.load_data()
        self.rank_sites()
        return self.df
    
    
'''
ranking = SiteRanking(str(WEEKLY_KPIS_FILE))
ranked_df = ranking.run()

best, worst = ranking.get_best_worst_latest_week()

print("\nBest site by cost efficiency:")
print(best[["site_name", "cost_per_kwh", "rank_efficiency"]])

latest_week = ranked_df["week_start"].max()
latest = ranked_df[ranked_df["week_start"] == latest_week]

print("\nHighest consumption sites:")
print(
    latest.sort_values("rank_consumption")
    [["site_name", "weekly_total_consumption", "rank_consumption"]]
    .head(3)
)

print("\nLargest week-over-week increases:")
print(
    latest.sort_values("rank_wow_increase")
    [["site_name", "wow_change_percent", "rank_wow_increase"]]
    .head(3)
)

'''
