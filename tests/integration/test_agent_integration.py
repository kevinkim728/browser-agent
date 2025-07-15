"""
Integration tests for the complete agent with controlled environment.

Tests agent decision-making, tool usage, and error handling with proper verification.
"""

import pytest
import os
import asyncio  # Add this
from unittest.mock import AsyncMock, MagicMock, patch
from agents import Runner  # Add this
from browser_agent_final.core_agent import create_browser_agent
from browser_agent_final.classes import AgentConfig, ExecutionAction, ActionType
from browser_agent_final.browser_tools import navigate_to, click_element, type_text


class MockBrowserSession:
    """Mock browser session that tracks tool calls for integration testing."""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset all tracking state."""
        self.tool_calls = []
        self.current_url = "about:blank"
        self.page_title = "New Tab"
        self.page_responses = {}
        self.error_scenarios = {}
        self.call_count = 0
        
    def setup_page_response(self, url: str, title: str = None, content: str = None, 
                           elements: list = None, should_fail: bool = False):
        """Setup controlled response for a specific page."""
        self.page_responses[url] = {
            "title": title or "Test Page",
            "content": content or "<html><body>Test content</body></html>",
            "elements": elements or [],
            "should_fail": should_fail
        }
        
    def setup_error_scenario(self, tool_name: str, error_message: str):
        """Setup error scenario for specific tool."""
        self.error_scenarios[tool_name] = error_message
        
    async def mock_navigate_to(self, url: str) -> ExecutionAction:
        """Mock navigation with controlled responses."""
        self.call_count += 1
        call_info = {
            "tool": "navigate_to",
            "args": {"url": url},
            "call_order": self.call_count
        }
        self.tool_calls.append(call_info)
        
        # Check for error scenarios
        if "navigate_to" in self.error_scenarios:
            return ExecutionAction(
                current_url=self.current_url,
                page_title=self.page_title,
                success=False,
                action_type=ActionType.NAVIGATE,
                instruction=f"navigate to {url}",
                execution_details=self.error_scenarios["navigate_to"],
                page_changed=False,
                result_data=None,
                action_taken=None
            )
        
        # Normal success case
        if url in self.page_responses:
            response = self.page_responses[url]
            if response["should_fail"]:
                return ExecutionAction(
                    current_url=self.current_url,
                    page_title=self.page_title,
                    success=False,
                    action_type=ActionType.NAVIGATE,
                    instruction=f"navigate to {url}",
                    execution_details="Navigation failed",
                    page_changed=False,
                    result_data=None,
                    action_taken=None
                )
            
            self.current_url = url
            self.page_title = response["title"]
            return ExecutionAction(
                current_url=url,
                page_title=response["title"],
                success=True,
                action_type=ActionType.NAVIGATE,
                instruction=f"navigate to {url}",
                execution_details=None,
                page_changed=True,
                result_data=None,
                action_taken=None
            )
        
        # Default response for unknown URLs
        self.current_url = url
        self.page_title = "Unknown Page"
        return ExecutionAction(
            current_url=url,
            page_title="Unknown Page",
            success=True,
            action_type=ActionType.NAVIGATE,
            instruction=f"navigate to {url}",
            execution_details=None,
            page_changed=True,
            result_data=None,
            action_taken=None
        )
    
    async def mock_click_element(self, instruction: str) -> ExecutionAction:
        """Mock element clicking with controlled responses."""
        self.call_count += 1
        call_info = {
            "tool": "click_element",
            "args": {"instruction": instruction},
            "call_order": self.call_count
        }
        self.tool_calls.append(call_info)
        
        # Check for error scenarios
        if "click_element" in self.error_scenarios:
            return ExecutionAction(
                current_url=self.current_url,
                page_title=self.page_title,
                success=False,
                action_type=ActionType.CLICK,
                instruction=instruction,
                execution_details=self.error_scenarios["click_element"],
                page_changed=False,
                result_data=None,
                action_taken=None
            )
        
        # Simulate different click outcomes based on instruction
        if "submit" in instruction.lower():
            # Fixed: Update mock's internal state
            self.current_url = self.current_url + "/submitted"
            return ExecutionAction(
                current_url=self.current_url,  # Use updated URL
                page_title=self.page_title,
                success=True,
                action_type=ActionType.CLICK,
                instruction=instruction,
                execution_details="Clicked submit button",
                page_changed=True,
                result_data={"clicked": "submit"},
                action_taken="click"
            )
        else:
            return ExecutionAction(
                current_url=self.current_url,
                page_title=self.page_title,
                success=True,
                action_type=ActionType.CLICK,
                instruction=instruction,
                execution_details="Clicked element",
                page_changed=False,
                result_data={"clicked": "element"},
                action_taken="click"
            )
    
    async def mock_type_text(self, instruction: str) -> ExecutionAction:
        """Mock text typing with controlled responses."""
        self.call_count += 1
        call_info = {
            "tool": "type_text",
            "args": {"instruction": instruction},
            "call_order": self.call_count
        }
        self.tool_calls.append(call_info)
        
        # Check for error scenarios
        if "type_text" in self.error_scenarios:
            return ExecutionAction(
                current_url=self.current_url,
                page_title=self.page_title,
                success=False,
                action_type=ActionType.TYPE,
                instruction=instruction,
                execution_details=self.error_scenarios["type_text"],
                page_changed=False,
                result_data=None,
                action_taken=None
            )
        
        # Extract text being typed (basic parsing)
        typed_text = "sample text"
        if "'" in instruction:
            typed_text = instruction.split("'")[1]
        elif '"' in instruction:
            typed_text = instruction.split('"')[1]
        
        return ExecutionAction(
            current_url=self.current_url,
            page_title=self.page_title,
            success=True,
            action_type=ActionType.TYPE,
            instruction=instruction,
            execution_details=f"Typed: {typed_text}",
            page_changed=False,
            result_data={"typed": typed_text},
            action_taken="type"
        )
    
    def get_tool_calls(self) -> list:
        """Get all tool calls made during testing."""
        return self.tool_calls
    
    def get_call_sequence(self) -> list:
        """Get the sequence of tool names called."""
        return [call["tool"] for call in self.tool_calls]
    
    def was_tool_called(self, tool_name: str) -> bool:
        """Check if a specific tool was called."""
        return tool_name in self.get_call_sequence()
    
    def get_tool_args(self, tool_name: str) -> dict:
        """Get arguments for the last call to a specific tool."""
        for call in reversed(self.tool_calls):
            if call["tool"] == tool_name:
                return call["args"]
        return {}


@pytest.fixture
def mock_browser():
    """Create a mock browser session for controlled testing."""
    return MockBrowserSession()


@pytest.mark.asyncio
class TestAgentIntegrationSimplified:
    """Simplified integration tests that focus on tool behavior without LLM calls."""
    
    async def test_navigate_tool_with_controlled_response(self, mock_browser):
        """Test navigation tool with controlled response."""
        # Setup controlled response
        mock_browser.setup_page_response(
            "https://example.com", 
            title="Example Domain",
            content="<h1>Example Domain</h1>"
        )
        
        # Call the mock directly
        result = await mock_browser.mock_navigate_to("https://example.com")
        
        # Verify tool call tracking
        assert mock_browser.was_tool_called("navigate_to")
        assert mock_browser.get_tool_args("navigate_to")["url"] == "https://example.com"
        
        # Verify response
        assert result.success is True
        assert result.action_type == ActionType.NAVIGATE
        assert result.current_url == "https://example.com"
        assert result.page_title == "Example Domain"
        assert result.page_changed is True
    
    async def test_click_tool_with_controlled_response(self, mock_browser):
        """Test click tool with controlled response."""
        # Setup initial state
        mock_browser.current_url = "https://test.com"
        mock_browser.page_title = "Test Page"
        
        # Call the mock
        result = await mock_browser.mock_click_element("click the submit button")
        
        # Verify tool call tracking
        assert mock_browser.was_tool_called("click_element")
        assert mock_browser.get_tool_args("click_element")["instruction"] == "click the submit button"
        
        # Verify response
        assert result.success is True
        assert result.action_type == ActionType.CLICK
        assert result.current_url == "https://test.com/submitted"  # URL changed for submit
        assert result.page_changed is True
        assert result.result_data["clicked"] == "submit"
    
    async def test_type_tool_with_controlled_response(self, mock_browser):
        """Test type tool with controlled response."""
        # Setup initial state
        mock_browser.current_url = "https://form.com"
        mock_browser.page_title = "Form Page"
        
        # Call the mock
        result = await mock_browser.mock_type_text("type 'john@example.com' in the email field")
        
        # Verify tool call tracking
        assert mock_browser.was_tool_called("type_text")
        assert mock_browser.get_tool_args("type_text")["instruction"] == "type 'john@example.com' in the email field"
        
        # Verify response
        assert result.success is True
        assert result.action_type == ActionType.TYPE
        assert result.current_url == "https://form.com"
        assert result.page_changed is False
        assert result.result_data["typed"] == "john@example.com"
    
    async def test_multi_step_tool_sequence(self, mock_browser):
        """Test sequence of tool calls."""
        # Setup page response
        mock_browser.setup_page_response(
            "https://workflow.com",
            title="Workflow Page",
            content="<form><input name='email'/><button>Submit</button></form>"
        )
        
        # Execute sequence
        nav_result = await mock_browser.mock_navigate_to("https://workflow.com")
        type_result = await mock_browser.mock_type_text("type 'test@example.com' in email field")
        click_result = await mock_browser.mock_click_element("click the submit button")
        
        # Verify sequence
        call_sequence = mock_browser.get_call_sequence()
        assert call_sequence == ["navigate_to", "type_text", "click_element"]
        
        # Verify each step
        assert nav_result.success is True
        assert type_result.success is True
        assert click_result.success is True
        
        # Verify final state
        assert mock_browser.current_url == "https://workflow.com/submitted"
    
    async def test_error_handling_scenarios(self, mock_browser):
        """Test error handling in tools."""
        # Setup error scenario
        mock_browser.setup_error_scenario("navigate_to", "Network timeout")
        
        # Call tool that should fail
        result = await mock_browser.mock_navigate_to("https://failing-site.com")
        
        # Verify error handling
        assert result.success is False
        assert result.execution_details == "Network timeout"
        assert result.page_changed is False
        
        # Verify call was tracked
        assert mock_browser.was_tool_called("navigate_to")
    
    async def test_tool_call_order_tracking(self, mock_browser):
        """Test that tool calls are tracked in correct order."""
        # Make multiple calls
        await mock_browser.mock_navigate_to("https://step1.com")
        await mock_browser.mock_click_element("click button")
        await mock_browser.mock_type_text("type text")
        await mock_browser.mock_navigate_to("https://step2.com")
        
        # Verify order
        tool_calls = mock_browser.get_tool_calls()
        assert len(tool_calls) == 4
        
        # Verify call order
        assert tool_calls[0]["tool"] == "navigate_to"
        assert tool_calls[0]["call_order"] == 1
        assert tool_calls[1]["tool"] == "click_element"
        assert tool_calls[1]["call_order"] == 2
        assert tool_calls[2]["tool"] == "type_text"
        assert tool_calls[2]["call_order"] == 3
        assert tool_calls[3]["tool"] == "navigate_to"
        assert tool_calls[3]["call_order"] == 4
    
    async def test_mock_reset_functionality(self, mock_browser):
        """Test that mock reset works correctly."""
        # Make some calls
        await mock_browser.mock_navigate_to("https://test.com")
        await mock_browser.mock_click_element("click button")
        
        # Verify calls were made
        assert len(mock_browser.get_tool_calls()) == 2
        
        # Reset and verify clean state
        mock_browser.reset()
        assert len(mock_browser.get_tool_calls()) == 0
        assert mock_browser.current_url == "about:blank"
        assert mock_browser.page_title == "New Tab"
        assert mock_browser.call_count == 0


@pytest.mark.asyncio
class TestToolIntegration:
    """Test actual tool integration without agent."""
    
    async def test_actual_tool_structure(self):
        """Test that actual tools have correct structure."""
        from browser_agent_final.browser_tools import navigate_to, click_element, type_text
        
        # Verify tools are FunctionTool objects with correct attributes
        assert hasattr(navigate_to, 'name')
        assert hasattr(navigate_to, 'on_invoke_tool')
        assert hasattr(click_element, 'name')
        assert hasattr(click_element, 'on_invoke_tool')
        assert hasattr(type_text, 'name')
        assert hasattr(type_text, 'on_invoke_tool')
        
        # Verify tool names
        assert navigate_to.name == "navigate_to"
        assert click_element.name == "click_element"
        assert type_text.name == "type_text"
        
        # Verify they have callable invoke methods
        assert callable(navigate_to.on_invoke_tool)
        assert callable(click_element.on_invoke_tool)
        assert callable(type_text.on_invoke_tool)
    
    async def test_agent_creation_with_tools(self):
        """Test that agent is created with correct tools."""
        config = AgentConfig(
            model="gpt-4o-mini",
            temperature=0.1,
            max_turns=5
        )
        
        agent = create_browser_agent(config)
        
        # Verify agent has tools
        assert hasattr(agent, 'tools')
        assert len(agent.tools) == 3
        
        # Verify tool names
        tool_names = [tool.name for tool in agent.tools]
        assert "navigate_to" in tool_names
        assert "click_element" in tool_names
        assert "type_text" in tool_names


@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
class TestAgentIntegrationReal:
    """Real LLM integration tests with timeouts."""
    
    async def test_agent_navigation_with_real_llm(self, controlled_agent, mock_browser):
        """Test agent navigation with real LLM decision-making."""
        # Setup controlled page response
        mock_browser.setup_page_response(
            "https://example.com", 
            title="Example Domain",
            content="<h1>Example Domain</h1><p>This domain is for use in illustrative examples.</p>"
        )
        
        task = "Navigate to https://example.com and tell me the page title"
        
        # Run the agent with timeout
        try:
            result = await asyncio.wait_for(
                Runner.run(controlled_agent, task, max_turns=3),
                timeout=30.0  # 30 second timeout
            )
            
            # Verify specific tool calls
            assert mock_browser.was_tool_called("navigate_to")
            
            # Verify correct URL was navigated to
            nav_args = mock_browser.get_tool_args("navigate_to")
            assert nav_args["url"] == "https://example.com"
            
            # Verify agent got the page title
            assert result is not None
            assert "Example Domain" in result.final_output
            
        except asyncio.TimeoutError:
            pytest.fail("Agent took too long to respond (>30s)")
    
    async def test_agent_multi_step_with_real_llm(self, controlled_agent, mock_browser):
        """Test agent performing multi-step task with real LLM."""
        # Setup controlled environment
        mock_browser.setup_page_response(
            "https://test-form.com",
            title="Test Form",
            content="<form><input name='search'/><button type='submit'>Search</button></form>"
        )
        
        task = "Go to https://test-form.com, type 'selenium testing' in the search field, and click submit"
        
        # Run with timeout
        try:
            result = await asyncio.wait_for(
                Runner.run(controlled_agent, task, max_turns=5),
                timeout=60.0  # Longer timeout for multi-step
            )
            
            # Verify correct tool sequence
            call_sequence = mock_browser.get_call_sequence()
            expected_sequence = ["navigate_to", "type_text", "click_element"]
            assert call_sequence == expected_sequence
            
            # Verify tool arguments
            type_args = mock_browser.get_tool_args("type_text")
            assert "selenium testing" in type_args["instruction"]
            
        except asyncio.TimeoutError:
            pytest.fail("Agent took too long to respond (>60s)")
    
    async def test_agent_error_handling_with_real_llm(self, controlled_agent, mock_browser):
        """Test agent's error handling with real LLM."""
        # Setup navigation to fail
        mock_browser.setup_error_scenario("navigate_to", "Network timeout")
        
        task = "Navigate to https://failing-site.com and describe the page"
        
        # Run the agent with timeout
        try:
            result = await asyncio.wait_for(
                Runner.run(controlled_agent, task, max_turns=3),
                timeout=30.0
            )
            
            # Verify agent attempted navigation
            assert mock_browser.was_tool_called("navigate_to")
            
            # Verify agent handled the error appropriately
            assert result is not None
            assert ("error" in result.final_output.lower() or 
                    "failed" in result.final_output.lower() or 
                    "timeout" in result.final_output.lower())
            
        except asyncio.TimeoutError:
            pytest.fail("Agent took too long to respond (>30s)")

class MockPage:
    """Mock page object that simulates Stagehand page interface."""
    
    def __init__(self, mock_browser):
        self.mock_browser = mock_browser
        self.url = mock_browser.current_url
        self._title = mock_browser.page_title
    
    async def goto(self, url):
        """Mock navigation."""
        result = await self.mock_browser.mock_navigate_to(url)
        self.url = result.current_url
        self._title = result.page_title
        if not result.success:
            raise Exception(result.execution_details)
    
    async def title(self):
        """Mock title retrieval."""
        return self._title
    
    async def act(self, instruction, timeout_ms=10000):
        """Mock page actions (click, type, etc.)."""
        # Determine action type based on instruction
        if any(word in instruction.lower() for word in ['click', 'button', 'link']):
            result = await self.mock_browser.mock_click_element(instruction)
        elif any(word in instruction.lower() for word in ['type', 'enter', 'input']):
            result = await self.mock_browser.mock_type_text(instruction)
        else:
            # Default to click
            result = await self.mock_browser.mock_click_element(instruction)
        
        # Update page state
        self.url = result.current_url
        self._title = result.page_title
        
        # Return a mock result object that matches Stagehand's interface
        class MockResult:
            def __init__(self, success, message, action):
                self.success = success
                self.message = message
                self.action = action
        
        return MockResult(
            success=result.success,
            message=result.execution_details or "Action completed",
            action=result.action_taken or "mock_action"
        )


@pytest.fixture
async def controlled_agent(mock_browser, monkeypatch):
    """Create an agent with controlled browser environment."""
    
    # Create mock page
    mock_page = MockPage(mock_browser)
    
    # Mock the browser session's get_page method
    async def mock_get_page():
        return mock_page
    
    # Patch the browser session
    monkeypatch.setattr("browser_agent_final.session.browser_session.get_page", mock_get_page)
    
    # Now create the agent - it will use the real tools but with mocked browser session
    from browser_agent_final.core_agent import create_browser_agent
    
    config = AgentConfig(
        model="gpt-4o-mini",
        temperature=0.1,
        max_turns=10
    )
    
    agent = create_browser_agent(config)
    
    # Reset mock state before each test
    mock_browser.reset()
    
    return agent