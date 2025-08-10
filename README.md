# Research Papers MCP Server

A Model Context Protocol (MCP) server that provides tools for searching and managing research papers from arXiv.

## Features

- **Search Papers**: Search for research papers on arXiv by topic
- **Extract Info**: Get detailed information about specific papers
- **List Topics**: View all research topics that have been searched
- **Paper Count**: Get statistics on papers per topic

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file with your OpenAI API key (for the chatbot):

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the MCP Server

### Method 1: Direct Testing

Test the server functionality:

```bash
python test_mcp_server.py
```

### Method 2: Run Server Directly

```bash
python mcp_server.py
```

### Method 3: Using MCP Inspector (Recommended for Testing)

1. **Install MCP Inspector**:
   ```bash
   npm install -g @modelcontextprotocol/inspector
   ```

2. **Run the Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector uv run mcp_server.py
   ```

- ***Alternatively***:
2. **Run with Inspector**:
   ```bash
   mcp-inspector --config mcp_config.json
   ```

3. **Alternative Inspector Command**:
   ```bash
   mcp-inspector --server research-papers python mcp_server.py
   ```

## Available Tools

### 1. `search_papers`
Search for papers on arXiv based on a topic.

**Parameters:**
- `topic` (string, required): The topic to search for
- `max_results` (integer, optional): Maximum number of results (default: 5)

**Example:**
```json
{
  "topic": "differential geometry",
  "max_results": 3
}
```

### 2. `extract_info`
Get detailed information about a specific paper.

**Parameters:**
- `paper_id` (string, required): The arXiv paper ID

**Example:**
```json
{
  "paper_id": "1310.7911v2"
}
```

### 3. `list_topics`
List all available research topics.

**Parameters:** None

### 4. `get_paper_count`
Get paper counts for topics.

**Parameters:**
- `topic` (string, optional): Specific topic to count (if not provided, counts all topics)

**Example:**
```json
{
  "topic": "differential geometry"
}
```

## Testing with MCP Inspector

1. **Start the Inspector**:
   ```bash
   mcp-inspector --config mcp_config.json
   ```

2. **Test Commands**:
   - Search for papers: `search_papers("artificial intelligence", 3)`
   - List topics: `list_topics()`
   - Get paper count: `get_paper_count()`
   - Extract paper info: `extract_info("1310.7911v2")`

## Integration with Chatbot

The MCP server can be integrated with your existing chatbot (`chatbot.py`) by:

1. Running the MCP server as a separate process
2. Using an MCP client library to connect to the server
3. Calling the tools through the MCP protocol

## File Structure

```
.
├── mcp_server.py          # Main MCP server
├── chatbot.py             # OpenAI chatbot with function calling
├── test_mcp_server.py     # Test script for the server
├── mcp_config.json        # MCP Inspector configuration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── papers/               # Directory for stored paper data
    └── {topic}/          # Topic-specific directories
        └── papers_info.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
2. **Permission Errors**: Ensure you have write permissions for the `papers/` directory
3. **Network Issues**: Check your internet connection for arXiv API calls
4. **MCP Inspector Not Found**: Install with `npm install -g @modelcontextprotocol/inspector`

### Debug Mode

Enable debug logging by modifying the logging level in `mcp_server.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## API Reference

The server implements the Model Context Protocol (MCP) specification and provides:

- **Tool Discovery**: Automatic tool registration and schema generation
- **Error Handling**: Comprehensive error handling and logging
- **Data Persistence**: Papers are stored locally in JSON format
- **Topic Organization**: Papers are organized by search topics

## License

This project is licensed under the MIT License - see the LICENSE file for details.


## TO TEST: 
- $ npm install -g @modelcontextprotocol/inspector
- $ npx @modelcontextprotocol/inspector uv run mcp_server.py

## TEST DOCUMENTATION

1. ![mcp-inspector.png](https://github.com/sulaiman-shamasna/MCP-Build-Rich-Context-AI-Apps-with-OpenAI/blob/main/docs/mcp-inspector.png)
2. ![mcp-tools.png](https://github.com/sulaiman-shamasna/MCP-Build-Rich-Context-AI-Apps-with-OpenAI/blob/main/docs/mcp-tools.png)
3. ![mcp-tools-test.png](https://github.com/sulaiman-shamasna/MCP-Build-Rich-Context-AI-Apps-with-OpenAI/blob/main/docs/mcp-tools-test.png)
4. ![mcp-tools-test-with-paper-id.png](https://github.com/sulaiman-shamasna/MCP-Build-Rich-Context-AI-Apps-with-OpenAI/blob/main/docs/mcp-tools-test-with-paper-id.png)