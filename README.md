# Browser Automation Agent

A web-based chat interface for automating browser interactions using natural language commands. Built with Chainlit, OpenAI Agents, and Stagehand.

## Overview

This tool provides a chat interface where you can control a web browser through natural language instructions. Type commands like "go to Amazon and search for headphones" and the agent will navigate websites, click elements, fill forms, and extract data automatically.

**Key Features:**
- **Intelligent feedback system** - Agent receives structured data about each action's success and results
- **Real element detection** - Knows exactly what elements were found and interacted with
- **Reliable execution** - Proper timeout configuration and error handling  
- **Adaptive behavior** - Makes informed decisions based on actual browser state

## Installation

Requirements:
- Python 3.12+
- OpenAI API key
- [uv](https://docs.astral.sh/uv/) package manager

```bash
git clone <repository-url>
cd browser_agent
uv sync
```

Create a `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Usage

Start the application:
```bash
chainlit run python main.py
```

Open http://localhost:8000 in your browser and start giving commands through the chat interface.

### Example Commands

- `Navigate to https://example.com`
- `Click the login button`
- `Type "john@example.com" in the email field`
- `Scroll down to see more content`
- `Extract all product names from this page`
- `Go back to the previous page`

## Project Structure

```
browser_agent/
├── main.py                # Chainlit web interface
├── browser_agent_final/   # Core automation logic
│   ├── agents.py          # AI agent configuration
│   ├── browser_tools.py   # Browser automation tools
│   ├── session.py         # Browser session management
│   └── classes.py         # Data models and types
└── pyproject.toml         # Project dependencies
```

## How it Works

1. User enters a command in the web chat interface
2. OpenAI agent interprets the command and plans actions
3. Agent executes actions using three core tools:
   - `navigate_to` - Navigate to URLs
   - `click_element` - Click buttons, links, and elements  
   - `type_text` - Type text into input fields
4. Browser actions are performed via Stagehand with structured feedback
5. Agent analyzes real execution results (success, element descriptions, selectors)
6. Results and next steps are returned to the chat interface

### Structured Feedback System
Each browser action returns an `ActResult` with:
- **Success status** - Whether the action worked
- **Element description** - Rich details about what was found/acted upon
- **Execution details** - Technical info including actual selectors used
- **Real-time analysis** - Agent adapts based on actual results, not assumptions

## Dependencies

- **Chainlit** - Web chat interface
- **OpenAI Agents** - AI agent framework
- **Stagehand** - Browser automation library
- **Pydantic** - Data validation and settings

## Configuration

The agent can be configured through the `AgentConfig` and `BrowserConfig` classes in `browser_agent_final/classes.py`. Default settings include:
- **10-second action timeouts** (using correct `timeout_ms` parameter)
- **10-second DOM settle timeout** for page stabilization  
- **Headless browser mode** (configurable)
- **1920x1080 viewport**
- **Local browser environment** with full debugging capabilities

## Limitations

- Requires internet connection for AI model calls
- Some websites may block automated interactions
- Complex authentication flows may require manual intervention
