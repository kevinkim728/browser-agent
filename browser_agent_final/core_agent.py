'''
Browser automation agent setup and configuration.

This module contains the main agent definition and instructions.
'''
from agents import Agent, ModelSettings
from datetime import datetime
from .classes import AgentConfig
from .browser_tools import navigate_to, click_element, type_text


def create_browser_agent(config: AgentConfig = None) -> Agent:
    """
    Create and configure the browser automation agent.
    
    Args:
        config: Agent configuration options
        
    Returns:
        Configured Agent instance
    """
    config = config or AgentConfig()
    
    planning_agent_instructions = f"""
You are a browser automation agent that completes web tasks step by step using natural language instructions.
Today's date is {datetime.now().strftime("%Y-%m-%d")}. This is important for date specific tasks.

**AVAILABLE TOOLS:**
1. navigate_to - Navigate to any URL
2. click_element - Click on elements 
3. type_text - Type text into fields

**PROMPTING STRUCTURE:**
- Use: [Article] + [Element Identity] + [Functional Description]
- Examples:
    - "click the search button that initiates queries"
    - "type 'text' into the input field where users enter data"
- Add spatial context only when disambiguation is needed:
    - Example:"click the search button in the header that initiates queries"
- Be atomic and specific. Let Stagehand determine when spatial context is necessary.
- This structure mirrors Stagehand's natural language patterns for optimal targeting.
- Only include one action per turn.
- Use natural language a human would understand

Your process:
1. Analyze the user's task
2. Use the most appropriate tool
3. **CRITICALLY IMPORTANT**: After each tool call, analyze the ExecutionAction response:
   - success: Whether the action worked
   - action_taken: The action that was taken
   - execution_details: Specific details about the execution of the action
   - page_changed: For actions expecting to change the page, check if the page changed
   - result_data: Full returned data by the action (if any)

NEVER use technical selectors or DOM references

"""

    tools = [navigate_to, click_element, type_text]
    
    return Agent(
        name="browser_automation_agent",
        instructions=planning_agent_instructions,
        model=config.model,
        tools=tools,
        model_settings=ModelSettings(temperature=config.temperature),
    )


# Create default agent instance
browser_agent = create_browser_agent()


__all__ = ["create_browser_agent", "browser_agent"]
