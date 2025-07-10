import random
from typing import Any
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
    
    return f"Stats for {player_name}: {runs} runs, 50 {wickets} (mock data). {leader}"

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
        base.AssistantMessage("Review the last 10 matches of this team and provide information about - best bowlers, best batsmen, best all rounder.")
    ]    
    
if __name__ == "__main__":
    mcp.run(transport='stdio') 