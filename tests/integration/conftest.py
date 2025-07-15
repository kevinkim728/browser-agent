"""
Shared fixtures for integration tests.

Provides controlled browser environments and test utilities.
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch
from browser_agent_final.session import BrowserSession
from browser_agent_final.classes import BrowserConfig, AgentConfig
from browser_agent_final.core_agent import create_browser_agent


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def browser_session():
    """Create a real browser session for testing (for real integration tests)."""
    config = BrowserConfig(
        headless=True,  # Run headless for CI/testing
        viewport_width=1280,
        viewport_height=720,
        timeout=10000
    )
    
    session = BrowserSession(config)
    yield session
    
    # Cleanup
    await session.close()


@pytest.fixture
async def browser_page(browser_session):
    """Get a real browser page for testing."""
    page = await browser_session.get_page()
    yield page
    # Session cleanup handled by browser_session fixture


@pytest.fixture
def test_agent():
    """Create a test agent with fast settings (for real LLM tests)."""
    config = AgentConfig(
        model="gpt-4o-mini",  # Use cheaper model for testing
        temperature=0.1,      # Lower temperature for consistent results
        max_turns=5           # Limit turns for faster tests
    )
    
    return create_browser_agent(config)


@pytest.fixture
def test_urls():
    """Provide test URLs for integration testing."""
    return {
        "simple": "https://example.com",
        "google": "https://www.google.com",
        "form": "https://httpbin.org/forms/post",
        "json": "https://httpbin.org/json",
        "slow": "https://httpbin.org/delay/2"
    }


# Test markers available:
# pytest.mark.slow - for slow tests
# pytest.mark.integration - for integration tests
# pytest.mark.controlled - for controlled environment tests