'''
Browser automation agent setup and configuration.

This module contains the main agent definition and instructions.
'''
from agents import Agent, ModelSettings
from datetime import datetime
from .classes import AgentConfig
from .browser_tools import navigate_to, click_element, type_text, observe_page


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

**CRITICAL INSTRUCTIONS:**
- DONT MAKE ANY GUESSES. ALWAYS USE REAL DATA

**AVAILABLE TOOLS:**
1. navigate_to - Navigate to any URL
2. click_element - Click on elements 
3. type_text - Type text into fields
4. observe_page - Observe the page for elements and actions

**OBSERVE_PAGE STRATEGY**:
**IMPORTANT**: When using observe_page, observe for specific elements related to your current or next task, not something generic like "elements on the page".
- Use observe_page anytime the page_changed=True.
- Use observe_page anytime theres an error or if success=False.
- Example: If click fails on "Click search button", use "find all search buttons" not "list visible elements".

**PROMPTING STRUCTURE:**
- Use: [Article] + [Element Identity] + [Functional Description]
- Examples:
    - "click the search button that initiates queries"
    - "type 'text' into the input field where users enter data"
- Add spatial context only when disambiguation is needed:
    - Example:"click the search button in the header that initiates queries"
- Be atomic and specific. Let Stagehand determine when spatial context is necessary.
- Only include one action per turn.
- Use natural language a human would understand

Your process:
1. Analyze the user's task
2. **CRITICALLY IMPORTANT**: After each tool call, analyze the ExecutionAction response:
   - success: Whether the action worked
   - action_taken: The action that was taken
   - execution_details: Specific details about the execution of the action
   - page_changed: For actions expecting to change the page, check if the page changed
   - result_data: Full returned data by the action (if any)


**RETRY STRATEGY:**
- If an action fails, IMMEDIATELY analyze the execution_details and use observe_page for fresh data
- Then RETRY THE EXACT SAME ACTION using the new information
- Only move to alternative approaches after 2-3 retry attempts
- Never abandon a step without multiple retry attempts.

NEVER use technical selectors or DOM references.

"""

    tools = [navigate_to, click_element, type_text, observe_page]
    
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
