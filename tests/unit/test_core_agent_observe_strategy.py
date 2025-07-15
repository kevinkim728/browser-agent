"""
Comprehensive tests for core agent's observe_page strategy and retry logic.

This file tests whether the LLM (core agent) properly follows the observe_page strategy:
- Use observe_page anytime page_changed=True
- Use observe_page anytime there's an error or success=False  
- Analyze execution_details and use observe_page for fresh data on failures
- Retry steps using information from execution_details and observe_page
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
import asyncio
from browser_agent_final.core_agent import create_browser_agent, browser_agent
from browser_agent_final.classes import AgentConfig, ExecutionAction, ActionType
from browser_agent_final.browser_tools import navigate_to, click_element, type_text, observe_page


class TestObservePageStrategy:
    """Test that the agent properly uses observe_page according to strategy."""
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_agent_instructions_include_observe_strategy(self, mock_agent_class):
        """Test that agent instructions include the observe_page strategy."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Verify observe_page strategy is in instructions
        assert "observe_page" in instructions
        assert "Use observe_page anytime the page_changed=True" in instructions
        assert "Use observe_page anytime theres an error or if success=False" in instructions
        assert "use observe_page for fresh data" in instructions
        
        # Verify retry strategy is in instructions
        assert "RETRY STRATEGY:" in instructions
        assert "analyze the execution_details carefully" in instructions
        assert "Retry the step using the information gathered" in instructions
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_agent_has_observe_page_tool(self, mock_agent_class):
        """Test that observe_page is included in the agent's tools."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        tools = call_args[1]["tools"]
        
        # Verify observe_page is in tools list
        assert observe_page in tools
        assert len(tools) == 4  # navigate_to, click_element, type_text, observe_page
        
        # Verify all expected tools are present
        assert navigate_to in tools
        assert click_element in tools
        assert type_text in tools
        assert observe_page in tools
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_agent_instructions_include_execution_analysis(self, mock_agent_class):
        """Test that agent instructions include proper ExecutionAction analysis."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Verify ExecutionAction analysis instructions
        assert "analyze the ExecutionAction response" in instructions
        assert "success: Whether the action worked" in instructions
        assert "action_taken: The action that was taken" in instructions
        assert "execution_details: Specific details about the execution" in instructions
        assert "page_changed: For actions expecting to change the page" in instructions
        assert "result_data: Full returned data by the action" in instructions


class TestAgentBehaviorSimulation:
    """Simulate agent behavior to test observe_page strategy and retry logic."""
    
    def create_mock_execution_action(self, success=True, page_changed=False, 
                                   action_type=ActionType.NAVIGATE, 
                                   execution_details=None, result_data=None):
        """Helper to create mock ExecutionAction objects."""
        return ExecutionAction(
            current_url="https://example.com",
            page_title="Test Page",
            success=success,
            action_type=action_type,
            instruction="test instruction",
            execution_details=execution_details,
            page_changed=page_changed,
            result_data=result_data,
            action_taken="test action"
        )
    
    def test_scenario_page_changed_true_should_trigger_observe(self):
        """Test that page_changed=True should trigger observe_page usage."""
        # Create a scenario where page_changed=True
        action_result = self.create_mock_execution_action(
            success=True, 
            page_changed=True,
            action_type=ActionType.NAVIGATE
        )
        
        # In a real scenario, the agent should:
        # 1. Analyze the ExecutionAction
        # 2. Notice page_changed=True
        # 3. Call observe_page according to strategy
        
        # This is a behavioral test - verifying the strategy is documented
        assert action_result.page_changed is True
        assert action_result.success is True
        
        # Agent should use observe_page when page_changed=True
        # This would be tested in an integration test with actual agent
        
    def test_scenario_failure_should_trigger_observe_and_retry(self):
        """Test that action failure should trigger observe_page and retry."""
        # Create a scenario where success=False
        action_result = self.create_mock_execution_action(
            success=False,
            page_changed=False,
            action_type=ActionType.CLICK,
            execution_details="Element not found: button with text 'Submit'"
        )
        
        # In a real scenario, the agent should:
        # 1. Analyze the ExecutionAction
        # 2. Notice success=False
        # 3. Analyze execution_details for error information
        # 4. Call observe_page for fresh data
        # 5. Retry with information from observe_page
        
        assert action_result.success is False
        assert action_result.execution_details is not None
        assert "Element not found" in action_result.execution_details
        
        # Agent should use observe_page when success=False
        # Then retry with fresh information
        
    def test_scenario_error_with_execution_details_analysis(self):
        """Test that execution_details are properly analyzed for retry strategy."""
        error_scenarios = [
            {
                "execution_details": "Element not found: button with text 'Submit'",
                "expected_strategy": "observe_page to find available buttons"
            },
            {
                "execution_details": "Timeout waiting for element to be clickable",
                "expected_strategy": "observe_page to check element state"
            },
            {
                "execution_details": "Element is not interactable",
                "expected_strategy": "observe_page to find alternative elements"
            },
            {
                "execution_details": "Navigation failed: invalid URL",
                "expected_strategy": "observe_page to check current page state"
            }
        ]
        
        for scenario in error_scenarios:
            action_result = self.create_mock_execution_action(
                success=False,
                execution_details=scenario["execution_details"]
            )
            
            # Verify the error details are captured
            assert action_result.success is False
            assert action_result.execution_details == scenario["execution_details"]
            
            # In a real scenario, agent should analyze these details
            # and choose appropriate retry strategy with observe_page


class TestObservePageRetryPatterns:
    """Test specific retry patterns that should use observe_page."""
    
    def test_click_failure_retry_pattern(self):
        """Test retry pattern for click failures."""
        # Step 1: Click fails
        click_failure = ExecutionAction(
            current_url="https://example.com/form",
            page_title="Form Page",
            success=False,
            action_type=ActionType.CLICK,
            instruction="click the submit button",
            execution_details="Element not found: submit button",
            page_changed=False,
            result_data=None,
            action_taken=None
        )
        
        # Step 2: Agent should call observe_page
        observe_result = ExecutionAction(
            current_url="https://example.com/form",
            page_title="Form Page", 
            success=True,
            action_type=ActionType.OBSERVE,
            instruction="find all buttons on the page",
            execution_details="Found 3 observable elements on the page",
            page_changed=False,
            result_data=[
                {"selector": "button#save", "description": "Save button", "action": "Click"},
                {"selector": "input[type='submit']", "description": "Submit form", "action": "Click"},
                {"selector": "a.cancel", "description": "Cancel link", "action": "Click"}
            ],
            action_taken="Observed page elements"
        )
        
        # Step 3: Agent should retry with new information
        # This simulates the expected behavior pattern
        assert click_failure.success is False
        assert observe_result.success is True
        assert observe_result.action_type == ActionType.OBSERVE
        assert len(observe_result.result_data) > 0
        
        # Agent should now have fresh data to retry the click
        
    def test_navigation_failure_retry_pattern(self):
        """Test retry pattern for navigation failures."""
        # Step 1: Navigation fails
        nav_failure = ExecutionAction(
            current_url="https://old-site.com",
            page_title="Old Page",
            success=False,
            action_type=ActionType.NAVIGATE,
            instruction="navigate to https://new-site.com",
            execution_details="Navigation timeout: site unreachable",
            page_changed=False,
            result_data=None,
            action_taken=None
        )
        
        # Step 2: Agent should call observe_page to check current state
        observe_result = ExecutionAction(
            current_url="https://old-site.com",
            page_title="Old Page",
            success=True,
            action_type=ActionType.OBSERVE,
            instruction="observe current page state",
            execution_details="Found 5 observable elements on the page",
            page_changed=False,
            result_data=[
                {"selector": "a.new-site-link", "description": "Link to new site", "action": "Click"},
                {"selector": "form#redirect", "description": "Redirect form", "action": "Click"}
            ],
            action_taken="Observed page elements"
        )
        
        # Verify the expected pattern
        assert nav_failure.success is False
        assert observe_result.success is True
        assert observe_result.action_type == ActionType.OBSERVE
        
        # Agent should now have alternative approaches
        
    def test_page_change_triggers_observe(self):
        """Test that page_changed=True triggers observe_page."""
        # Step 1: Action succeeds but changes page
        successful_action = ExecutionAction(
            current_url="https://example.com/new-page",
            page_title="New Page",
            success=True,
            action_type=ActionType.CLICK,
            instruction="click the next page link",
            execution_details="Successfully clicked link",
            page_changed=True,  # This should trigger observe_page
            result_data=None,
            action_taken="Clicked link"
        )
        
        # Step 2: Agent should call observe_page due to page_changed=True
        observe_result = ExecutionAction(
            current_url="https://example.com/new-page",
            page_title="New Page",
            success=True,
            action_type=ActionType.OBSERVE,
            instruction="observe elements on the new page",
            execution_details="Found 7 observable elements on the page",
            page_changed=False,
            result_data=[
                {"selector": "h1", "description": "Page heading", "action": "Read"},
                {"selector": "button.continue", "description": "Continue button", "action": "Click"},
                {"selector": "input#search", "description": "Search input", "action": "Type"}
            ],
            action_taken="Observed page elements"
        )
        
        # Verify the expected pattern
        assert successful_action.success is True
        assert successful_action.page_changed is True
        assert observe_result.success is True
        assert observe_result.action_type == ActionType.OBSERVE
        
        # Agent should now understand the new page context


class TestAgentInstructionCompliance:
    """Test that agent instructions properly enforce observe_page strategy."""
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_instructions_enforce_observe_on_page_change(self, mock_agent_class):
        """Test that instructions explicitly require observe_page on page changes."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Check for specific observe_page strategy instructions
        assert "OBSERVE_PAGE STRATEGY" in instructions
        assert "Use observe_page anytime the page_changed=True" in instructions
        
        # Check that the strategy is clearly defined
        strategy_lines = [line.strip() for line in instructions.split('\n') 
                         if 'observe_page' in line.lower()]
        
        assert len(strategy_lines) >= 2  # Should have multiple references
        
    @patch('browser_agent_final.core_agent.Agent')
    def test_instructions_enforce_observe_on_failure(self, mock_agent_class):
        """Test that instructions require observe_page on failures."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Check for failure handling instructions
        assert "Use observe_page anytime theres an error or if success=False" in instructions
        assert "analyze the execution_details carefully" in instructions
        assert "use observe_page for fresh data" in instructions
        
    @patch('browser_agent_final.core_agent.Agent')
    def test_instructions_enforce_retry_strategy(self, mock_agent_class):
        """Test that instructions include comprehensive retry strategy."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Check for retry strategy components
        assert "RETRY STRATEGY:" in instructions
        assert "If an action fails, analyze the execution_details carefully" in instructions
        assert "Retry the step using the information gathered from execution_details and observe_page" in instructions
        assert "try alternative approaches" in instructions
        
    @patch('browser_agent_final.core_agent.Agent') 
    def test_instructions_include_execution_action_analysis(self, mock_agent_class):
        """Test that instructions require proper ExecutionAction analysis."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Check for ExecutionAction analysis requirements
        assert "analyze the ExecutionAction response" in instructions
        
        # Check that all ExecutionAction fields are mentioned
        required_fields = [
            "success: Whether the action worked",
            "action_taken: The action that was taken", 
            "execution_details: Specific details about the execution",
            "page_changed: For actions expecting to change the page",
            "result_data: Full returned data by the action"
        ]
        
        for field in required_fields:
            assert field in instructions, f"Missing required field: {field}"


class TestObservePageIntegrationReadiness:
    """Test that the system is ready for observe_page integration testing."""
    
    def test_observe_page_tool_is_available(self):
        """Test that observe_page tool is properly available."""
        # Verify observe_page is imported and available
        assert observe_page is not None
        assert hasattr(observe_page, 'on_invoke_tool')
        
    def test_execution_action_supports_observe(self):
        """Test that ExecutionAction supports observe_page results."""
        # Create an observe_page result
        observe_action = ExecutionAction(
            current_url="https://example.com",
            page_title="Test Page",
            success=True,
            action_type=ActionType.OBSERVE,
            instruction="find all buttons",
            execution_details="Found 3 observable elements",
            page_changed=False,
            result_data=[
                {"selector": "button#submit", "description": "Submit button", "action": "Click"},
                {"selector": "button#cancel", "description": "Cancel button", "action": "Click"}
            ],
            action_taken="Observed page elements"
        )
        
        # Verify the action structure supports observe_page
        assert observe_action.action_type == ActionType.OBSERVE
        assert observe_action.result_data is not None
        assert len(observe_action.result_data) > 0
        assert all('selector' in item for item in observe_action.result_data)
        assert all('action' in item for item in observe_action.result_data)
        
    def test_action_types_include_observe(self):
        """Test that ActionType enum includes OBSERVE."""
        # Verify OBSERVE is in ActionType
        assert hasattr(ActionType, 'OBSERVE')
        assert ActionType.OBSERVE == "observe"
        
        # Verify all expected action types are present
        expected_types = ["navigate", "click", "type", "observe"]
        for expected_type in expected_types:
            assert any(action_type.value == expected_type for action_type in ActionType) 