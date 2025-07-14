import asyncio
import logging
import os
import queue
import threading

import streamlit as st
from dotenv import load_dotenv
from gemini_tool_agent.agent import Agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Setup logging
logger = logging.getLogger("mcp_client_chat")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# Stream (console) handler
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Global result queue for thread communication
result_queue = queue.Queue()


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


load_dotenv()
api_key = os.environ.get("GEMINI_KEY")

st.set_page_config(page_title="Curious Kode MCP Chat", layout="centered")
st.title("Curious Kode MCP Chat")

# Initialize chat history and pending response
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_response" not in st.session_state:
    st.session_state.pending_response = None
if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False

# Display chat history (after processing)
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


# Helper to call MCP tool asynchronously
def run_async_in_thread(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    loop.close()
    result_queue.put(result)  # Only put the result in the queue!
    st.session_state.awaiting_response = False


async def call_mcp_agent(user_input):
    logger.info(f"User input: {user_input}")
    agent = Agent(api_key)
    # Connect to MCP server
    server_path = "mcp_server.py"
    server_params = StdioServerParameters(
        command="uv", args=["run", "python", server_path]
    )
    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()
            # Get and set tools for the agent
            response = await session.list_tools()
            tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in response.tools
            ]
            agent.tools = tools
            logger.info(f"Available tools: {[tool['name'] for tool in tools]}")
            # Now process the query
            response = agent.process_query(user_input)
            agent.history.append({"role": "user", "content": user_input})

            if isinstance(response, dict) and response.get("needs_tool", False):
                tool_name = response.get("tool_name", None)
                if tool_name:
                    logger.info(f"Calling MCP tool: {tool_name}")
                    tool_response = agent.process_use_tool(tool_name)
                    agent.history.append(
                        {"role": "assistant", "content": tool_response}
                    )
                    call_tool = agent.process_use_tool(tool_name)
                    agent.history.append(
                        {"role": "process_tool_call", "content": call_tool}
                    )
                    result = await session.call_tool(tool_name, call_tool["input"])
                    agent.history.append(
                        {"role": "tool_call_result", "content": result}
                    )
                    parsed = parse_mcp_result(result)
                    logger.info(f"Parsed MCP tool response: {parsed}")
                    return parsed
            if isinstance(response, dict) and response.get(
                "needs_direct_response", False
            ):
                agent.history.append(
                    {"role": "direct_response", "content": response["direct_response"]}
                )
                logger.info("Direct response...")
                return response["direct_response"]
            # Fallback: generate a response
            conversation_context = (
                agent.history[-5:] if len(agent.history) >= 5 else agent.history
            )
            response_text = agent.generate_response(
                f"""
                You are a helpful assistant responding to the following query:
                QUERY: {user_input}
                CONVERSATION HISTORY: {conversation_context}
                Please provide accurate response that considers the conversation history and response from the MCP server.
                If you are not able to generate a response then mention that this is the limit to the response based on MCP server.
                """
            )
            agent.history.append({"role": "assistant", "content": response_text})
            logger.info(f"Generated fallback response: {response_text}")
            return response_text


# User input
if prompt := st.chat_input("Ask about cricket predictions or stats..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    st.session_state.awaiting_response = True
    thread = threading.Thread(
        target=run_async_in_thread,
        args=(call_mcp_agent(prompt),),
    )
    thread.start()

while True:
    try:
        result = result_queue.get_nowait()
    except queue.Empty:
        result = None
    if result is not None:
        st.session_state.messages.append({"role": "assistant", "content": result})
        st.chat_message("assistant").write(result)
        st.session_state.awaiting_response = False
