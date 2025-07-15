"""
Browser automation tools for web interaction.

This module contains all the function tools that the agent can use
to interact with web pages through Stagehand.

"""
from agents import function_tool
from .classes import ExecutionAction, ActionType
from .session import browser_session
import asyncio

@function_tool
async def navigate_to(url: str) -> ExecutionAction:
    """
    Navigate to a URL
    """
    try:
        page = await browser_session.get_page()
        
        await page.goto(url)
        await asyncio.sleep(3)

        return ExecutionAction(
            current_url=page.url,
            page_title=await page.title(),
            success=True,
            action_type=ActionType.NAVIGATE,
            instruction=f"navigate to {url}",
            execution_details=None,
            page_changed=True,
            result_data=None,
            action_taken=None
        )
        
    except Exception as e:
        return ExecutionAction(
            current_url=None,
            page_title=None,
            success=False,
            action_type=ActionType.NAVIGATE,
            instruction=f"navigate to {url}",
            execution_details=str(e),
            page_changed=False,
            result_data=None,
            action_taken=None
        )


@function_tool
async def click_element(instruction: str) -> ExecutionAction:
    """
    Click on an element described in natural language
    """
    try:
        page = await browser_session.get_page()
        current_url_before = page.url 
        
        await asyncio.sleep(2)
        result = await page.act(instruction, timeout_ms=10000)
        await asyncio.sleep(2)
        
        current_url_after = page.url
        page_changed = current_url_before != current_url_after 
        
        return ExecutionAction(
            current_url=page.url,
            page_title=await page.title(),
            success=result.success,
            action_type=ActionType.CLICK,
            instruction=instruction,
            execution_details=result.message,
            result_data=result,
            page_changed=page_changed,
            action_taken=result.action
        )
        
    except Exception as e:
        page = await browser_session.get_page()
        return ExecutionAction(
            current_url=page.url,
            page_title=await page.title(),
            success=False,
            action_type=ActionType.CLICK,
            instruction=instruction,
            execution_details=str(e),
            result_data=None,
            page_changed=False,
            action_taken=None
        )

@function_tool
async def type_text(instruction: str) -> ExecutionAction:
    """Type text into a field described in natural language"""
    try:
        page = await browser_session.get_page()
        
        # Execute the typing action
        await asyncio.sleep(2)
        result = await page.act(instruction, timeout_ms=10000)
        await asyncio.sleep(2)
        
        # Get current page state
        current_url = page.url
        page_title = await page.title()
        
        return ExecutionAction(
            current_url=current_url,
            page_title=page_title,
            success=result.success,
            action_type=ActionType.TYPE,
            instruction=instruction,
            result_data=result,
            execution_details=result.message,
            page_changed=False,
            action_taken=result.action
        )
        
    except Exception as e:
        page = await browser_session.get_page()
        current_url = page.url
        page_title = await page.title()
        
        return ExecutionAction(
            current_url=current_url,
            page_title=page_title,
            success=False,
            action_type=ActionType.TYPE,
            instruction=instruction,
            result_data=None,
            execution_details=str(e),
            page_changed=False,
            action_taken=None
        )
    
@function_tool
async def observe_page(instruction: str) -> ExecutionAction:
    """
    Observe is used to get a list of actions that can be taken on the current page. 
    If you are looking for a specific element, you can also pass in an instruction to observe.
    Observe can also return a suggested action for the candidate element.
    """
    try:
        page = await browser_session.get_page()
        

        elements = await page.observe(instruction=instruction, return_action=True)
        await asyncio.sleep(5)
        
        
        return ExecutionAction(
            current_url=page.url,
            page_title=await page.title(),
            success=True,
            action_type=ActionType.OBSERVE,
            instruction=instruction,
            execution_details=f"Found {len(elements)} observable elements on the page",
            page_changed=False,
            result_data=elements,
            action_taken=f"Observed page elements with instruction: {instruction}"
        )
        
    except Exception as e:
        page = await browser_session.get_page()
        return ExecutionAction(
            current_url=page.url,
            page_title=await page.title(),
            success=False,
            action_type=ActionType.OBSERVE,
            instruction=instruction,
            execution_details=str(e),
            page_changed=False,
            result_data=None,
            action_taken=None
        )
    

@function_tool
async def extract_page(instruction: str) -> ExecutionAction:
    """
    Extract is used to extract data from the current page.
    """
    try:
        page = await browser_session.get_page()
        

        extract_result = await page.extract(instruction=instruction)
        await asyncio.sleep(3)
        
        
        return ExecutionAction(
            current_url=page.url,
            page_title=await page.title(),
            success=True,
            action_type=ActionType.EXTRACT,
            instruction=instruction,
            execution_details=f"Extracted data from the page",
            page_changed=False,
            result_data=extract_result,
            action_taken=f"Extracted data from the page with instruction: {instruction}"
        )
        
    except Exception as e:
        page = await browser_session.get_page()
        return ExecutionAction(
            current_url=page.url,
            page_title=await page.title(),
            success=False,
            action_type=ActionType.EXTRACT,
            instruction=instruction,
            execution_details=str(e),
            page_changed=False,
            result_data=None,
            action_taken=None
        )



# Export all tools
__all__ = [
    "navigate_to",
    "click_element",
    "type_text",
    "observe_page",
    "extract_page"
]
