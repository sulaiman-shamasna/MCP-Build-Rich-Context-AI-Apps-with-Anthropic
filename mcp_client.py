from dotenv import load_dotenv
import openai
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List
import asyncio
import nest_asyncio
import json

nest_asyncio.apply()

load_dotenv()

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession = None
        self.openai_client = openai.OpenAI()
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        messages = [{'role':'user', 'content':query}]
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=self.available_tools,
            max_tokens=2024
        )
        process_query = True
        while process_query:
            assistant_message = response.choices[0].message
            assistant_content = assistant_message.content
            
            if assistant_content:
                print(assistant_content)
                messages.append({'role': 'assistant', 'content': assistant_content})
                
                if not assistant_message.tool_calls:
                    process_query = False
                    continue
            
            if assistant_message.tool_calls:
                messages.append({'role': 'assistant', 'content': assistant_content, 'tool_calls': assistant_message.tool_calls})
                
                for tool_call in assistant_message.tool_calls:
                    tool_id = tool_call.id
                    tool_args = tool_call.function.arguments
                    tool_name = tool_call.function.name
    
                    print(f"Calling tool {tool_name} with args {tool_args}")
                    
                    # Parse tool_args from JSON string to dictionary
                    try:
                        tool_args_dict = json.loads(tool_args)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing tool arguments: {e}")
                        tool_args_dict = {}
                    
                    # tool invocation through the client session
                    result = await self.session.call_tool(tool_name, arguments=tool_args_dict)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": result.content
                    })
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=self.available_tools,
                    max_tokens=2024
                )
                
                if not response.choices[0].message.tool_calls:
                    print(response.choices[0].message.content)
                    process_query = False

    
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    break
                    
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="uv",  # Executable
            args=["run", "mcp_server.py"],  # Optional command line arguments
            env=None,  # Optional environment variables
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()
    
                # List available tools
                response = await session.list_tools()
                
                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])
                
                self.available_tools = [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                } for tool in response.tools]
    
                await self.chat_loop()


async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()
  

if __name__ == "__main__":
    asyncio.run(main())