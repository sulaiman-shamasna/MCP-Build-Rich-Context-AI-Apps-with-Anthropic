# MCP Summary

## Architecture Overview

This overview of the Model Context Protocol (MCP) discusses its scope and core concepts, and provides an example demonstrating each core concept. Because MCP SDKs abstract away many concerns, most developers will likely find the data layer protocol section to be the most useful. It discusses how MCP servers can provide context to an AI application. For specific implementation details, please refer to the documentation for your language-specific SDK.

## Scope

The Model Context Protocol includes the following projects:
- **MCP Specification**: A specification of MCP that outlines the implementation requirements for clients and servers.
- **MCP SDKs**: SDKs for different programming languages that implement MCP.
- **MCP Development Tools**: Tools for developing MCP servers and clients, including the MCP Inspector.
- **MCP Reference Server Implementations**: Reference implementations of MCP servers.

MCP focuses solely on the protocol for context exchange—it does not dictate how AI applications use LLMs or manage the provided context.

## Concepts of MCP
### Participants

MCP follows a client-server architecture where an MCP host—an AI application like Claude Code or Claude Desktop—establishes connections to one or more MCP servers. The key participants in the MCP architecture are:
- **MCP Host**: The AI application that coordinates and manages one or multiple MCP clients.
- **MCP Client**: A component that maintains a connection to an MCP server and obtains context from an MCP server for the MCP host to use.
- **MCP Server**: A program that provides context to MCP clients.

### Layers

MCP consists of two layers:
- **Data Layer**: Defines the JSON-RPC based protocol for client-server communication, including lifecycle management and core primitives, such as tools, resources, prompts, and notifications.
- **Transport Layer**: Defines the communication mechanisms and channels that enable data exchange between clients and servers.

Conceptually, the data layer is the inner layer, while the transport layer is the outer layer.

## Conclusion
MCP leverages a structured client-server relationship to manage context data, making it essential for developers in AI applications.