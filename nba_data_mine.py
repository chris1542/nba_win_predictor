nba_data_mine.py


import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_advanced_stats(year):
    """
    Scrapes the advanced stats table for a given year from
    Basketball Reference and returns it as a pandas DataFrame.
    """
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_advanced.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Look for the table by its id. Often it's "advanced_stats" or "advanced".
    table = soup.find("table", {"id": "advanced_stats"})
    if table is None:
        table = soup.find("table", {"id": "advanced"})
    
    if table is None:
        print(f"Could not find the advanced stats table for {year}.")
        return None

    # Read the table into a DataFrame
    df = pd.read_html(str(table))[0]

    # Add a column for the season, e.g. 2022/2023 if year = 2023
    df["Season"] = f"{year-1}/{year}"
    return df

def main():
    # We’ll loop from 2023 down to 2000
    # Change the range if you want more or fewer years.
    start_year = 2024
    end_year = 2000

    all_dataframes = []
    for year in range(start_year, end_year - 1, -1):
        print(f"Scraping {year}...")
        df = scrape_advanced_stats(year)
        if df is not None:
            all_dataframes.append(df)

    # Concatenate all DataFrames into one
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        # Save to CSV
        combined_df.to_csv("nba_advanced_2000_to_2023.csv", index=False)
        print("Successfully saved combined data to nba_advanced_2000_to_2023.csv")
    else:
        print("No dataframes were found. Check if the table IDs have changed.")

if __name__ == "__main__":
    main()

df=pd.read_csv('/Users/collinsch/Desktop/iReady Analysis/nba_advanced_2000_to_2024.csv')

df.columns
# Ensure the necessary columns are numeric
df["OWS"] = pd.to_numeric(df["OWS"], errors="coerce")
df["DWS"] = pd.to_numeric(df["DWS"], errors="coerce")
df["Age"] = pd.to_numeric(df["Age"], errors="coerce")
# Create a combined contribution column for ranking (using OWS + DWS)
df["Contrib"] = df["OWS"] + df["DWS"]

def agg_team_stats(group):
    # Sort players by combined contributions (highest first)
    group_sorted = group.sort_values(by="Contrib", ascending=False)
    
    # For top player subsets, if team has fewer players than the threshold,
    # use all available players
    def top_avg_age(n):
        if len(group_sorted) >= n:
            return group_sorted.head(n)["Age"].mean()
        else:
            return group_sorted["Age"].mean()

    def top_sum(n, col):
        if len(group_sorted) >= n:
            return group_sorted.head(n)[col].sum()
        else:
            return group_sorted[col].sum()

    return pd.Series({
        "top_2_avg_age": top_avg_age(2),
        "top_3_avg_age": top_avg_age(3),
        "top_5_avg_age": top_avg_age(5),
        "top_8_avg_age": top_avg_age(8),
        "top_2_sum_ows": top_sum(2, "OWS"),
        "top_3_sum_ows": top_sum(3, "OWS"),
        "top_5_sum_ows": top_sum(5, "OWS"),
        "top_8_sum_ows": top_sum(8, "OWS"),
        "top_2_sum_dws": top_sum(2, "DWS"),
        "top_3_sum_dws": top_sum(3, "DWS"),
        "top_5_sum_dws": top_sum(5, "DWS"),
        "top_8_sum_dws": top_sum(8, "DWS")
    })

# Group by Season and Team ('Tm') and apply the aggregation
result_df = df.groupby(["Season", "Team"]).apply(agg_team_stats).reset_index()

# Display the result
result_df.head()


import matplotlib.pyplot as plt
# Get a list of unique teams in the result dataframe
# Compute total win shares (OWS + DWS) for every Season-Team combination
team_totals = df.groupby(["Season", "Team"])["Contrib"].sum().reset_index().rename(columns={"Contrib": "total_contrib"})

for team in result_df["Team"].unique():
    # Filter aggregated data for the team and sort by Season
    team_data = result_df[result_df["Team"] == team].sort_values("Season")
    # Merge with total win shares computed from the original dataframe
    team_data = team_data.merge(team_totals, on=["Season", "Team"])

    # Calculate win share contributions for top 2, top 3, and top 5
    team_data["top2"] = team_data["top_2_sum_ows"] + team_data["top_2_sum_dws"]
    team_data["top3"] = team_data["top_3_sum_ows"] + team_data["top_3_sum_dws"]
    team_data["top5"] = team_data["top_5_sum_ows"] + team_data["top_5_sum_dws"]

    # Calculate percentages of total win share
    team_data["pct_top2"] = team_data["top2"] / team_data["total_contrib"] * 100
    team_data["pct_top3"] = team_data["top3"] / team_data["total_contrib"] * 100
    team_data["pct_top5"] = team_data["top5"] / team_data["total_contrib"] * 100

    # Create a plot of percentage contributions
    plt.figure(figsize=(10, 6))
    plt.plot(team_data["Season"], team_data["pct_top2"], marker="o", label="Top 2")
    plt.plot(team_data["Season"], team_data["pct_top3"], marker="o", label="Top 3")
    plt.plot(team_data["Season"], team_data["pct_top5"], marker="o", label="Top 5")
    plt.title(f"Team {team}: Win Share Split by Top 2, Top 3, & Top 5 Players")
    plt.xlabel("Season")
    plt.ylabel("Percentage of Total Win Shares (%)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()
