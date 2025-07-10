# Cricket Prediction MCP Server

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-ModelContextProtocol-blueviolet)](https://modelcontextprotocol.io/)
[![uv](https://img.shields.io/badge/uv-fast%20Python%20installer-brightgreen)](https://astral.sh/uv/)

This is a sample [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server built with Python, demonstrating how to expose tools and resources to LLMs and MCP clients.

## Features

- **Predict Winner Tool**: Predicts the winner between two cricket teams (mock logic).
- **Get Player Stats Tool**: Returns mock stats for a cricket player.
- **Match Data CSV Resource**: Exposes mock cricket match data as a CSV resource, with support for sampling rows.

## Setup

1. **Install [uv](https://astral.sh/uv/):**
   ```sh
   # Follow instructions at https://astral.sh/uv/
   ```
2. **Install dependencies:**
   ```sh
   uv venv
   uv add "mcp[cli]" httpx
   ```
3. **Run the server:**
   ```sh
   uv run mcp dev main.py
   ```

## Usage

This server exposes the following MCP tools and resources:

### Tools
- `predict_winner(team1: str, team2: str) -> str`: Predicts the winner between two teams (mock).
- `get_player_stats(player_name: str) -> str`: Returns mock stats for a player.

### Resources
- `match_data_csv(sampling: int = None) -> str`: Returns mock match data as CSV. If `sampling` is provided, returns that many random rows (plus header).

## About MCP

Model Context Protocol (MCP) standardizes how applications provide context and tools to LLMs. Learn more at [modelcontextprotocol.io](https://modelcontextprotocol.io/).

---

This project is for demonstration purposes only and uses mock data and logic.