import random
import re

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

# Initialize FastMCP server
mcp = FastMCP("cricket_prediction")


@mcp.tool()
async def predict_winner(team1: str, team2: str) -> str:
    """Predict the winner between two cricket teams (mock implementation).

    Args:
        team1: Name of the first team
        team2: Name of the second team
    """
    # Mock logic: just pick the first team for now
    winner = random.choice([team1, team2])
    return f"Predicted winner: {winner} (mock prediction)"


@mcp.tool()
async def get_player_stats(player_name: str) -> str:
    """Get mock stats for a cricket player.

    Args:
        player_name: Name of the player
    """
    # Mock stats
    runs = random.randint(0, 2000)
    wickets = random.randint(0, 100)
    leader = ""
    if runs > 1000 or wickets > 50:
        leader = "Top of the leader board!"

    return (
        f"Stats for {player_name}: {runs} runs, {wickets} wickets (mock data). {leader}"
    )


@mcp.tool()
async def get_indian_captian_information(player_name: str) -> str:
    """Get Information about an Indian Cricket Captian.

    Args:
        player_name: Name of the player
    """
    indian_captains = [
        {
            "name": "MS Dhoni",
            "trophies_won": 8,
            "years_as_captain": 9,
            "years_range": "2007–2016",
            "has_retired": True,
        },
        {
            "name": "Virat Kohli",
            "trophies_won": 5,
            "years_as_captain": 7,
            "years_range": "2014–2021",
            "has_retired": True,
        },
        {
            "name": "Sourav Ganguly",
            "trophies_won": 4,
            "years_as_captain": 5,
            "years_range": "2000–2005",
            "has_retired": True,
        },
        {
            "name": "Mohammad Azharuddin",
            "trophies_won": 3,
            "years_as_captain": 9,
            "years_range": "1990–1999",
            "has_retired": True,
        },
        {
            "name": "Kapil Dev",
            "trophies_won": 2,
            "years_as_captain": 5,
            "years_range": "1982–1987",
            "has_retired": True,
        },
        {
            "name": "Rahul Dravid",
            "trophies_won": 2,
            "years_as_captain": 2,
            "years_range": "2005–2007",
            "has_retired": True,
        },
        {
            "name": "Rohit Sharma",
            "trophies_won": 2,
            "years_as_captain": 2,
            "years_range": "2022–2024",
            "has_retired": False,
        },
        {
            "name": "Ajit Wadekar",
            "trophies_won": 2,
            "years_as_captain": 2,
            "years_range": "1971–1974",
            "has_retired": True,
        },
        {
            "name": "Sunil Gavaskar",
            "trophies_won": 1,
            "years_as_captain": 5,
            "years_range": "1976–1985",
            "has_retired": True,
        },
        {
            "name": "Anil Kumble",
            "trophies_won": 1,
            "years_as_captain": 1,
            "years_range": "2007–2008",
            "has_retired": True,
        },
    ]

    # Search for player_name in the list of dicts using regex (case-insensitive, partial match)
    pattern = re.compile(player_name, re.IGNORECASE)
    leader = None
    for d in indian_captains:
        if pattern.search(d["name"]):
            leader = d
            break

    if leader is not None:
        return f"Information about the Indian Cricket Captian {leader['name']}: {leader['trophies_won']} trophies, between {leader['years_range']} and {'has retired' if leader['has_retired'] else 'has not retired'}"
    else:
        return f"There is no information avaliable for {player_name} as an Indian Cricket Captian!"


@mcp.resource("teamstats://")
def match_data_csv() -> str:
    """Return mock match data as CSV file content."""
    csv_content = (
        "match_id,team1,team2,winner,score1,score2\n"
        "1,India,Australia,India,250,245\n"
        "2,England,South Africa,England,300,280\n"
        "3,Pakistan,New Zealand,New Zealand,220,225\n"
    )
    return csv_content


@mcp.prompt(title="Team Review")
def team_code(team: str) -> str:
    return [
        base.UserMessage("Review Team:"),
        base.UserMessage(team),
        base.AssistantMessage(
            "Review the last 10 matches of this team and provide information about - best bowlers, best batsmen, best all rounder."
        ),
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")
