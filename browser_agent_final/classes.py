"""
Pydantic models for browser automation agent.

This module contains all data models used throughout the application.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class ActionType(str, Enum):
    """Enumeration of possible browser actions."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"


class ExecutionAction(BaseModel):
    current_url: Optional[str] = Field(
        None, 
        description="The current URL after performing the action"
    )
    
    page_title: Optional[str] = Field(
        None, 
        description="The page title for context and navigation tracking"
    )
    
    success: bool = Field(
        description="Whether the action was successfully completed"
    )
    
    action_type: str = Field(
        description="Type of action performed"
    )
    
    instruction: Optional[str] = Field(
        None, 
        description="The natural language instruction that was executed"
    )
    
    execution_details: Optional[str] = Field(
        None, 
        description="Specific details about the execution of the action"
    )
    
    page_changed: bool = Field(
        False,
        description="Whether the action caused page changes"
    )

    result_data: Optional[Any] = Field(
        None,
        description="Any data returned by the action"
    )

    action_taken: Optional[str] = Field(
        None,
        description="The action that was taken"
    )


class BrowserConfig(BaseModel):
    """Configuration for browser session."""
    headless: bool = Field(default=False, description="Run browser in headless mode")
    viewport_width: int = Field(default=1920, description="Browser viewport width")
    viewport_height: int = Field(default=1080, description="Browser viewport height")
    timeout: int = Field(default=5000, description="Default timeout in milliseconds")


class AgentConfig(BaseModel):
    """Configuration for the browser automation agent."""
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    temperature: float = Field(default=0.3, description="Model temperature")
    max_turns: int = Field(default=20, description="Maximum conversation turns")
