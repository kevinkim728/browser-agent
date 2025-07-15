"""
Unit tests for browser_tools.py

Comprehensive testing with proper edge cases and error scenarios.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import Error as PlaywrightError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from browser_agent_final.browser_tools import navigate_to, click_element, type_text, observe_page
from browser_agent_final.classes import ExecutionAction, ActionType


class TestNavigateTo:
    """Comprehensive tests for navigate_to function."""
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_navigate_to_success(self, mock_get_page):
        """Test successful navigation with all state checks."""
        mock_page = AsyncMock()
        mock_page.goto.return_value = None
        mock_page.url = "https://google.com"
        mock_page.title.return_value = "Google"
        mock_get_page.return_value = mock_page
        
        # Test the actual function (need to access underlying function)
        # For now, test through the tool interface
        result = await navigate_to.on_invoke_tool(navigate_to, '{"url": "https://google.com"}')
        
        assert isinstance(result, ExecutionAction)
        assert result.success is True
        assert result.current_url == "https://google.com"
        assert result.page_title == "Google"
        assert result.action_type == ActionType.NAVIGATE
        assert result.page_changed is True
        assert result.execution_details is None
        
        # Verify function was called with correct parameters
        mock_page.goto.assert_called_once_with("https://google.com")
        mock_page.title.assert_called_once()
    
    @pytest.mark.parametrize("url,expected_success,description", [
        ("https://google.com", True, "Standard HTTPS URL"),
        ("http://example.com", True, "Standard HTTP URL"),  
        ("https://localhost:3000", True, "Localhost with port"),
        ("", False, "Empty URL"),
        ("not-a-url", False, "Invalid URL format"),
        ("javascript:alert('xss')", False, "XSS attempt"),
        ("ftp://example.com", True, "FTP URL (should work but might fail)"),
        ("https://" + "a" * 2000 + ".com", False, "Extremely long URL"),
    ])
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_navigate_to_various_urls(self, mock_get_page, url, expected_success, description):
        """Test navigation with various URL formats and edge cases."""
        mock_page = AsyncMock()
        
        if expected_success:
            mock_page.goto.return_value = None
            mock_page.url = url
            mock_page.title.return_value = "Test Page"
        else:
            mock_page.goto.side_effect = PlaywrightError(f"Invalid URL: {url}")
            mock_page.url = "about:blank"
            mock_page.title.return_value = "Error"
        
        mock_get_page.return_value = mock_page
        
        result = await navigate_to.on_invoke_tool(navigate_to, f'{{"url": "{url}"}}')
        
        assert result.success == expected_success, f"Failed for {description}: {url}"
        
        if expected_success:
            assert result.current_url == url
        else:
            assert result.execution_details is not None
    
    @pytest.mark.parametrize("error_type,error_message", [
        (PlaywrightTimeoutError, "Navigation timeout"),
        (PlaywrightError, "Network error"),
        (ConnectionError, "Connection refused"),
        (PermissionError, "Access denied"),
    ])
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_navigate_to_error_scenarios(self, mock_get_page, error_type, error_message):
        """Test different types of navigation errors."""
        mock_page = AsyncMock()
        mock_page.goto.side_effect = error_type(error_message)
        mock_get_page.return_value = mock_page
        
        result = await navigate_to.on_invoke_tool(navigate_to, '{"url": "https://failing-site.com"}')
        
        assert result.success is False
        assert result.current_url is None
        assert result.page_title is None
        assert error_message in result.execution_details
        assert result.page_changed is False
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page') 
    async def test_navigate_to_malformed_json(self, mock_get_page):
        """Test handling of malformed JSON input."""
        mock_page = AsyncMock()
        mock_get_page.return_value = mock_page
        
        # Test various malformed JSON scenarios
        malformed_inputs = [
            "invalid json",
            '{"url":}',  # Missing value
            '{"wrong_field": "https://google.com"}',  # Wrong field name
            '{}',  # Missing required field
            '',   # Empty string
        ]
        
        for bad_input in malformed_inputs:
            result = await navigate_to.on_invoke_tool(navigate_to, bad_input)
            assert isinstance(result, str), f"Should return error string for: {bad_input}"
            assert "error" in result.lower() or "invalid" in result.lower()


class TestClickElement:
    """Comprehensive tests for click_element function."""
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_click_element_success_with_timing_verification(self, mock_get_page):
        """Test successful click with proper timing and parameter verification."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        
        mock_act_result = MagicMock()
        mock_act_result.success = True
        mock_act_result.message = "Clicked successfully"
        mock_act_result.action = "click button"
        mock_page.act.return_value = mock_act_result
        
        mock_get_page.return_value = mock_page
        
        instruction = "click the submit button"
        result = await click_element.on_invoke_tool(click_element, f'{{"instruction": "{instruction}"}}')
        
        # Verify result
        assert result.success is True
        assert result.action_type == ActionType.CLICK
        assert result.instruction == instruction
        
        # Verify timing and parameters
        mock_page.act.assert_called_once_with(instruction, timeout_ms=10000)
    
    @pytest.mark.parametrize("instruction,expected_success", [
        ("click the submit button", True),
        ("click the login link in the header", True),
        ("", False),  # Empty instruction
        ("click the " + "x" * 1000 + " button", False),  # Extremely long instruction
        ("click <script>alert('xss')</script>", False),  # XSS attempt in instruction
    ])
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_click_element_instruction_validation(self, mock_get_page, instruction, expected_success):
        """Test click element with various instruction formats."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        
        mock_act_result = MagicMock()
        if expected_success:
            mock_act_result.success = True
            mock_act_result.message = "Success"
            mock_act_result.action = "clicked element"
        else:
            mock_act_result.success = False
            mock_act_result.message = "Invalid instruction"
            mock_act_result.action = None
        
        mock_page.act.return_value = mock_act_result
        mock_get_page.return_value = mock_page
        
        result = await click_element.on_invoke_tool(click_element, f'{{"instruction": "{instruction}"}}')
        
        assert result.success == expected_success

    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_click_element_page_change_detection(self, mock_get_page):
        """Test that page changes are properly detected."""
        mock_page = AsyncMock()
        mock_page.title.return_value = "New Page"
        
        # Simulate URL change during click
        url_before = "https://example.com"
        url_after = "https://example.com/new-page"
        
        def simulate_navigation(*args, **kwargs):
            mock_page.url = url_after
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.message = "Navigation occurred"
            mock_result.action = "click link"
            return mock_result
        
        mock_page.url = url_before
        mock_page.act.side_effect = simulate_navigation
        mock_get_page.return_value = mock_page
        
        result = await click_element.on_invoke_tool(click_element, '{"instruction": "click the navigation link"}')
        
        assert result.success is True
        assert result.page_changed is True
        assert result.current_url == url_after


class TestTypeText:
    """Comprehensive tests for type_text function."""
    
    @pytest.mark.parametrize("text_input,description", [
        ("Hello World", "Basic text"),
        ("", "Empty string"),
        ("Special chars: !@#$%^&*()", "Special characters"),
        ("Unicode: 你好世界", "Unicode characters"),
        ("Multi\nline\ntext", "Multi-line text"),
        ("Very " + "long " * 100 + "text", "Very long text"),
        ("'quotes' and \"double quotes\"", "Mixed quotes"),
    ])
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_type_text_various_inputs(self, mock_get_page, text_input, description):
        """Test typing with various text inputs."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        
        mock_act_result = MagicMock()
        mock_act_result.success = True
        mock_act_result.message = "Text typed successfully"
        mock_act_result.action = "typed text"
        mock_page.act.return_value = mock_act_result
        
        mock_get_page.return_value = mock_page
        
        # Escape the text input for JSON
        import json
        instruction = f"type '{text_input}' into the search box"
        json_input = json.dumps({"instruction": instruction})
        
        result = await type_text.on_invoke_tool(type_text, json_input)
        
        assert result.success is True, f"Failed for {description}: {text_input}"
        assert result.action_type == ActionType.TYPE
        assert result.page_changed is False  # Typing shouldn't change page


class TestObservePage:
    """Comprehensive tests for observe_page function."""
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_observe_page_success_basic(self, mock_get_page):
        """Test successful page observation with basic elements."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        
        # Mock observe method returning sample elements
        mock_elements = [
            {
                "selector": "button#submit",
                "description": "Submit button",
                "method": "click",
                "arguments": []
            },
            {
                "selector": "input[type='text']",
                "description": "Username input field",
                "method": "type",
                "arguments": ["text_to_type"]
            },
            {
                "selector": "a.nav-link",
                "description": "Navigation link",
                "method": "click",
                "arguments": []
            }
        ]
        
        mock_page.observe.return_value = mock_elements
        mock_get_page.return_value = mock_page
        
        instruction = "find all interactive elements"
        result = await observe_page.on_invoke_tool(observe_page, f'{{"instruction": "{instruction}"}}')
        
        # Verify result structure
        assert isinstance(result, ExecutionAction)
        assert result.success is True
        assert result.action_type == ActionType.OBSERVE
        assert result.instruction == instruction
        assert result.page_changed is False
        assert result.current_url == "https://example.com"
        assert result.page_title == "Test Page"
        assert "Found 3 observable elements" in result.execution_details
        assert result.action_taken == f"Observed page elements with instruction: {instruction}"
        
        # Verify result_data structure
        assert isinstance(result.result_data, list)
        assert len(result.result_data) == 3
        
        # Verify first element format
        first_element = result.result_data[0]
        assert first_element["selector"] == "button#submit"
        assert first_element["description"] == "Submit button"
        assert first_element["action"] == "Click"
        assert first_element["arguments"] == []
        
        # Verify observe method was called correctly
        mock_page.observe.assert_called_once_with(instruction=instruction, return_action=True)
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_observe_page_empty_results(self, mock_get_page):
        """Test observe_page when no elements are found."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Empty Page"
        mock_page.observe.return_value = []
        mock_get_page.return_value = mock_page
        
        instruction = "find submit buttons"
        result = await observe_page.on_invoke_tool(observe_page, f'{{"instruction": "{instruction}"}}')
        
        assert result.success is True
        assert result.action_type == ActionType.OBSERVE
        assert len(result.result_data) == 0
        assert "Found 0 observable elements" in result.execution_details
    
    @pytest.mark.parametrize("instruction,description", [
        ("find all buttons", "Basic button search"),
        ("locate login form", "Form-specific search"),
        ("find navigation links", "Navigation elements"),
        ("", "Empty instruction"),
        ("find all interactive elements on the page", "Long instruction"),
        ("find buttons with text 'Submit'", "Specific text search"),
        ("locate input fields for username", "Field-specific search"),
        ("find all clickable elements", "Action-specific search"),
    ])
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_observe_page_various_instructions(self, mock_get_page, instruction, description):
        """Test observe_page with various instruction types."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        
        # Mock different responses based on instruction
        mock_elements = [
            {
                "selector": "button.test",
                "description": "Test button",
                "method": "click",
                "arguments": []
            }
        ]
        
        mock_page.observe.return_value = mock_elements
        mock_get_page.return_value = mock_page
        
        # Escape instruction for JSON
        import json
        json_input = json.dumps({"instruction": instruction})
        
        result = await observe_page.on_invoke_tool(observe_page, json_input)
        
        assert result.success is True, f"Failed for {description}: {instruction}"
        assert result.instruction == instruction
        assert result.action_type == ActionType.OBSERVE
        
        # Verify observe was called with correct instruction
        mock_page.observe.assert_called_once_with(instruction=instruction, return_action=True)
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_observe_page_element_data_formatting(self, mock_get_page):
        """Test that element data is properly formatted in result_data."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        
        # Mock elements with various data structures
        mock_elements = [
            {
                "selector": "button#submit",
                "description": "Submit button",
                "method": "click",
                "arguments": []
            },
            {
                "selector": "input#username",
                "description": "Username field",
                "method": "type",
                "arguments": ["test_user"]
            },
            {
                # Missing optional fields
                "selector": "div.content",
                "method": "scroll"
            },
            {
                # All fields present
                "selector": "a.link",
                "description": "External link",
                "method": "click",
                "arguments": ["target_blank"]
            }
        ]
        
        mock_page.observe.return_value = mock_elements
        mock_get_page.return_value = mock_page
        
        result = await observe_page.on_invoke_tool(observe_page, '{"instruction": "find all elements"}')
        
        assert result.success is True
        assert len(result.result_data) == 4
        
        # Verify first element (all fields)
        element1 = result.result_data[0]
        assert element1["selector"] == "button#submit"
        assert element1["description"] == "Submit button"
        assert element1["action"] == "Click"
        assert element1["arguments"] == []
        
        # Verify second element (with arguments)
        element2 = result.result_data[1]
        assert element2["selector"] == "input#username"
        assert element2["description"] == "Username field"
        assert element2["action"] == "Type"
        assert element2["arguments"] == ["test_user"]
        
        # Verify third element (missing description)
        element3 = result.result_data[2]
        assert element3["selector"] == "div.content"
        assert element3["description"] == ""  # Should default to empty string
        assert element3["action"] == "Scroll"
        assert element3["arguments"] == ""  # Should default to empty string
    
    @pytest.mark.parametrize("error_type,error_message", [
        (PlaywrightTimeoutError, "Observation timeout"),
        (PlaywrightError, "Page observation error"),
        (ConnectionError, "Connection lost during observation"),
        (Exception, "General observation error"),
    ])
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_observe_page_error_scenarios(self, mock_get_page, error_type, error_message):
        """Test observe_page error handling for various error types."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        mock_page.observe.side_effect = error_type(error_message)
        mock_get_page.return_value = mock_page
        
        result = await observe_page.on_invoke_tool(observe_page, '{"instruction": "find buttons"}')
        
        assert result.success is False
        assert result.action_type == ActionType.OBSERVE
        assert result.current_url == "https://example.com"
        assert result.page_title == "Test Page"
        assert result.page_changed is False
        assert result.result_data is None
        assert result.action_taken is None
        assert error_message in result.execution_details
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_observe_page_malformed_json(self, mock_get_page):
        """Test handling of malformed JSON input."""
        mock_page = AsyncMock()
        mock_get_page.return_value = mock_page
        
        malformed_inputs = [
            "invalid json",
            '{"instruction":}',  # Missing value
            '{"wrong_field": "find buttons"}',  # Wrong field name
            '{}',  # Missing required field
            '',   # Empty string
        ]
        
        for bad_input in malformed_inputs:
            result = await observe_page.on_invoke_tool(observe_page, bad_input)
            assert isinstance(result, str), f"Should return error string for: {bad_input}"
            assert "error" in result.lower() or "invalid" in result.lower()
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_observe_page_method_name_capitalization(self, mock_get_page):
        """Test that method names are properly capitalized in the action field."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        
        # Test various method names
        mock_elements = [
            {"selector": "button", "method": "click", "description": "Button"},
            {"selector": "input", "method": "type", "description": "Input"},
            {"selector": "div", "method": "scroll", "description": "Div"},
            {"selector": "select", "method": "select", "description": "Select"},
            {"selector": "link", "method": "hover", "description": "Link"},
        ]
        
        mock_page.observe.return_value = mock_elements
        mock_get_page.return_value = mock_page
        
        result = await observe_page.on_invoke_tool(observe_page, '{"instruction": "find elements"}')
        
        assert result.success is True
        assert len(result.result_data) == 5
        
        # Verify capitalization
        expected_actions = ["Click", "Type", "Scroll", "Select", "Hover"]
        for i, expected_action in enumerate(expected_actions):
            assert result.result_data[i]["action"] == expected_action


# Integration-style tests (still unit tests but more realistic)
class TestBrowserToolsIntegration:
    """Integration-style tests for browser tools."""
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_sequential_actions_maintain_state(self, mock_get_page):
        """Test that sequential actions properly maintain page state."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Example Site"
        mock_get_page.return_value = mock_page
        
        # Mock successful navigation
        mock_page.goto.return_value = None
        
        # Mock successful click
        mock_click_result = MagicMock()
        mock_click_result.success = True
        mock_click_result.message = "Clicked"
        mock_click_result.action = "click"
        
        # Mock successful typing
        mock_type_result = MagicMock()
        mock_type_result.success = True
        mock_type_result.message = "Typed"
        mock_type_result.action = "type"
        
        mock_page.act.side_effect = [mock_click_result, mock_type_result]
        
        # Mock successful observation
        mock_observe_result = [
            {
                "selector": "button#submit",
                "description": "Submit button found",
                "method": "click",
                "arguments": []
            }
        ]
        
        mock_page.observe.return_value = mock_observe_result
        
        # Sequence: Navigate -> Observe -> Click -> Type
        nav_result = await navigate_to.on_invoke_tool(navigate_to, '{"url": "https://example.com"}')
        observe_result = await observe_page.on_invoke_tool(observe_page, '{"instruction": "find interactive elements"}')
        click_result = await click_element.on_invoke_tool(click_element, '{"instruction": "click login button"}')
        type_result = await type_text.on_invoke_tool(type_text, '{"instruction": "type username"}')
        
        # All should succeed
        assert nav_result.success is True
        assert observe_result.success is True
        assert click_result.success is True  
        assert type_result.success is True
        
        # Verify call sequence
        assert mock_page.goto.call_count == 1
        assert mock_page.observe.call_count == 1
        assert mock_page.act.call_count == 2


# Performance/timeout tests
class TestBrowserToolsPerformance:
    """Performance and timeout tests."""
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.browser_tools.browser_session.get_page')
    async def test_timeout_parameters_respected(self, mock_get_page):
        """Verify that timeout parameters are passed correctly."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Test Page"
        
        mock_act_result = MagicMock()
        mock_act_result.success = True
        mock_act_result.message = "Success"
        mock_act_result.action = "action completed"
        mock_page.act.return_value = mock_act_result
        
        mock_get_page.return_value = mock_page
        
        # Test click timeout
        await click_element.on_invoke_tool(click_element, '{"instruction": "click button"}')
        mock_page.act.assert_called_with("click button", timeout_ms=10000)
        
        # Test type timeout  
        await type_text.on_invoke_tool(type_text, '{"instruction": "type text"}')
        mock_page.act.assert_called_with("type text", timeout_ms=10000)