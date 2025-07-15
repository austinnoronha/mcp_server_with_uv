import os
from logging import getLogger

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from gemini_tool_agent.agent import Agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console

load_dotenv()
api_key = os.environ.get("GEMINI_KEY")

console = Console()

ascii_banner = r"""
   _____              _                      _  __           _       
  / ____|            (_)                    | |/ /          | |      
 | |     _   _  _ __  _   ___   _   _  ___  | ' /  ___    __| |  ___ 
 | |    | | | || '__|| | / _ \ | | | |/ __| |  <  / _ \  / _` | / _ \
 | |____| |_| || |   | || (_) || |_| |\__ \ | . \| (_) || (_| ||  __/
  \_____|\__,_||_|   |_| \___/  \__,_||___/ |_|\_\\___/  \__,_| \___|
                                                                     
                                                                     
"""

console.print("MCP Client Example", style="bold green")
console.print(ascii_banner, style="bold magenta")
console.print("Lets start FastAPI APP", style="bold green")
console.print("")
console.print("")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Use FastAPI/Uvicorn logger
logger = getLogger("uvicorn.error")


def parse_mcp_result(result):
    # If result is a dict with 'structuredContent'
    if hasattr(result, "structuredContent") and result.structuredContent:
        if (
            isinstance(result.structuredContent, dict)
            and "result" in result.structuredContent
        ):
            return result.structuredContent["result"]
    # If result has 'content' as a list of TextContent
    if hasattr(result, "content") and result.content:
        # Try to get the first text content
        first = result.content[0]
        if hasattr(first, "text"):
            return first.text
    # Fallback to string representation
    return str(result)


class MCPClient:
    def __init__(self, server_path="mcp_server.py"):
        self.server_path = server_path
        self.server_params = StdioServerParameters(
            command="uv", args=["run", "python", self.server_path]
        )
        self.agent = Agent(api_key)

    async def get_response(self, input: str):
        try:
            async with stdio_client(self.server_params) as (stdio, write):
                async with ClientSession(stdio, write) as session:
                    await session.initialize()
                    response = await session.list_tools()
                    tools = [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                        }
                        for tool in response.tools
                    ]
                    self.agent.tools = tools
                    logger.info(
                        "Connected to server with tools: %s",
                        [tool["name"] for tool in tools],
                    )

                    response = self.agent.process_query(input)
                    self.agent.history.append({"role": "user", "content": input})

                    if isinstance(response, dict) and response.get("needs_tool", False):
                        tool_name = response.get("tool_name", None)
                        logger.info(f"Model - tool_name: {tool_name}")
                        if tool_name:
                            tool_response = self.agent.process_use_tool(tool_name)
                            self.agent.history.append(
                                {"role": "assistant", "content": tool_response}
                            )
                            tool = tool_response["tool_name"]
                            logger.info(f"Model - tool: {tool}")
                            call_tool = self.agent.process_use_tool(tool)
                            self.agent.history.append(
                                {"role": "process_tool_call", "content": call_tool}
                            )
                            result = await session.call_tool(tool, call_tool["input"])
                            logger.info(f"Model - result: {result}")
                            self.agent.history.append(
                                {"role": "tool_call_result", "content": result}
                            )
                            return parse_mcp_result(result)
                    if isinstance(response, dict) and response.get(
                        "needs_direct_response", False
                    ):
                        self.agent.history.append(
                            {
                                "role": "direct_response",
                                "content": response["direct_response"],
                            }
                        )
                        logger.info(
                            f"Model - direct_response: {response['direct_response']}"
                        )
                        return response["direct_response"]
                    else:
                        conversation_context = (
                            self.agent.history[-5:]
                            if len(self.agent.history) >= 5
                            else self.agent.history
                        )
                        conversation_str = f"""
                        You are a helpful assistant responding to the following query:
                        QUERY: {input}
                        
                        CONVERSATION HISTORY: {conversation_context}
                        
                        Please provide accurate response that considers the conversation history and response from the.
                        If you are not able to genetate a response then mention that this is the limit to the response based on MCP server.
                        """
                        logger.info(f"conversation_str: {conversation_str}")
                        response_text = self.agent.generate_response(conversation_str)
                        self.agent.history.append(
                            {"role": "assistant", "content": response_text}
                        )
                        return response_text
        except Exception as e:
            logger.exception("An error occurred while processing your request")
            return f"An error occurred while processing your request: {str(e)}"


mcp_client = MCPClient()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat")
async def chat(message: str = Form(...)):
    # Basic message parsing for demo
    msg = message.lower()
    logger.info(f"Received message: {message}")
    try:
        response = await mcp_client.get_response(msg)
    except Exception as e:
        response = "NA"
        logger.exception(f"\nError occurred: {e}")
    if response:
        return JSONResponse({"reply": f"{str(response)}"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
