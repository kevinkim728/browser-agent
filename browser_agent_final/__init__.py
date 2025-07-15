"""
Browser Automation Agent

A modular browser automation system using AI agents and Stagehand.
"""

from .classes import ExecutionAction, ActionType, BrowserConfig, AgentConfig
from .session import browser_session, BrowserSession
from .core_agent import browser_agent, create_browser_agent
from .browser_tools import navigate_to, click_element, type_text, observe_page


__all__ = [
    # classes
    "ExecutionAction",
    "ActionType", 
    "BrowserConfig",
    "AgentConfig",
    
    # Session
    "browser_session",
    "BrowserSession",
    
    # Agent
    "browser_agent",
    "create_browser_agent",
    
    # browser_tools
    "navigate_to", "click_element", "type_text", "observe_page"
    ]
