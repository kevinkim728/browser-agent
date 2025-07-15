"""
Integration tests for observe_page strategy with real API calls.

Tests whether the LLM agent actually follows the observe_page strategy:
- Uses observe_page when page_changed=True
- Uses observe_page when success=False
- Analyzes execution_details for retry logic
- Makes real API calls to verify LLM behavior

These tests require:
- API keys for the LLM service
- Real browser sessions
- Internet connectivity
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from agents import Runner
from browser_agent_final.core_agent import create_browser_agent
from browser_agent_final.classes import AgentConfig, ExecutionAction, ActionType
from browser_agent_final.browser_tools import navigate_to, click_element, type_text, observe_page


class ObservePageTracker:
    """Track observe_page calls and analyze LLM behavior."""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset all tracking state."""
        self.observe_calls = []
        self.all_tool_calls = []
        self.page_changed_events = []
        self.failure_events = []
        self.retry_attempts = []
        
    def track_tool_call(self, tool_name: str, params: dict, result: ExecutionAction):
        """Track a tool call and its result."""
        call_info = {
            "tool": tool_name,
            "params": params,
            "result": result,
            "timestamp": len(self.all_tool_calls)
        }
        self.all_tool_calls.append(call_info)
        
        # Track specific events
        if tool_name == "observe_page":
            self.observe_calls.append(call_info)
            
        if result.page_changed:
            self.page_changed_events.append(call_info)
            
        if not result.success:
            self.failure_events.append(call_info)
            
    def should_have_observed_after_page_change(self) -> bool:
        """Check if observe_page was called after page_changed=True."""
        for i, call in enumerate(self.all_tool_calls):
            if call["result"].page_changed:
                # Check if next call is observe_page
                if i + 1 < len(self.all_tool_calls):
                    next_call = self.all_tool_calls[i + 1]
                    if next_call["tool"] == "observe_page":
                        return True
        return False
        
    def should_have_observed_after_failure(self) -> bool:
        """Check if observe_page was called after success=False."""
        for i, call in enumerate(self.all_tool_calls):
            if not call["result"].success:
                # Check if next call is observe_page
                if i + 1 < len(self.all_tool_calls):
                    next_call = self.all_tool_calls[i + 1]
                    if next_call["tool"] == "observe_page":
                        return True
        return False
        
    def get_summary(self) -> dict:
        """Get summary of tracked behavior."""
        return {
            "total_calls": len(self.all_tool_calls),
            "observe_calls": len(self.observe_calls),
            "page_changes": len(self.page_changed_events),
            "failures": len(self.failure_events),
            "followed_page_change_strategy": self.should_have_observed_after_page_change(),
            "followed_failure_strategy": self.should_have_observed_after_failure(),
            "tools_used": list(set(call["tool"] for call in self.all_tool_calls))
        }


@pytest.fixture
def observe_tracker():
    """Fixture providing observe_page behavior tracking."""
    return ObservePageTracker()


@pytest.fixture
def real_agent_with_tracking(observe_tracker):
    """Create a real agent with observe_page tracking."""
    config = AgentConfig(
        model="gpt-4o-mini",  # Use cheaper model for testing
        temperature=0.1,      # Lower temperature for consistent results
        max_turns=10          # Allow more turns for complex scenarios
    )
    
    agent = create_browser_agent(config)
    
    # Patch tools to track calls
    original_navigate = navigate_to.on_invoke_tool
    original_click = click_element.on_invoke_tool
    original_type = type_text.on_invoke_tool
    original_observe = observe_page.on_invoke_tool
    
    async def tracked_navigate(tool, params_str):
        params = json.loads(params_str)
        result = await original_navigate(tool, params_str)
        observe_tracker.track_tool_call("navigate_to", params, result)
        return result
        
    async def tracked_click(tool, params_str):
        params = json.loads(params_str)
        result = await original_click(tool, params_str)
        observe_tracker.track_tool_call("click_element", params, result)
        return result
        
    async def tracked_type(tool, params_str):
        params = json.loads(params_str)
        result = await original_type(tool, params_str)
        observe_tracker.track_tool_call("type_text", params, result)
        return result
        
    async def tracked_observe(tool, params_str):
        params = json.loads(params_str)
        result = await original_observe(tool, params_str)
        observe_tracker.track_tool_call("observe_page", params, result)
        return result
    
    # Apply patches
    navigate_to.on_invoke_tool = tracked_navigate
    click_element.on_invoke_tool = tracked_click
    type_text.on_invoke_tool = tracked_type
    observe_page.on_invoke_tool = tracked_observe
    
    yield agent
    
    # Restore original methods
    navigate_to.on_invoke_tool = original_navigate
    click_element.on_invoke_tool = original_click
    type_text.on_invoke_tool = original_type
    observe_page.on_invoke_tool = original_observe


@pytest.mark.integration
@pytest.mark.slow
class TestObservePageStrategyIntegration:
    """Integration tests for observe_page strategy with real API calls."""
    
    @pytest.mark.asyncio
    async def test_agent_uses_observe_page_after_navigation(self, real_agent_with_tracking, observe_tracker, test_urls):
        """Test that the LLM agent actually uses observe_page after navigation (page_changed=True)."""
        # Task that will cause page change
        task = f"Navigate to {test_urls['simple']} and observe what's on the page"
        
        # Execute task with real API calls
        result = await Runner.run(real_agent_with_tracking, task, max_turns=10)
        
        # Analyze the agent's behavior
        summary = observe_tracker.get_summary()
        
        # Verify strategy compliance
        assert summary["total_calls"] >= 2, "Should have made at least navigate + observe calls"
        assert summary["observe_calls"] >= 1, "Should have called observe_page at least once"
        assert summary["page_changes"] >= 1, "Should have had at least one page change"
        
        # CRITICAL: Check if agent followed the strategy
        if summary["page_changes"] > 0:
            assert summary["followed_page_change_strategy"], \
                "Agent should use observe_page after page_changed=True"
        
        # Verify tools used
        assert "navigate_to" in summary["tools_used"], "Should have used navigation"
        assert "observe_page" in summary["tools_used"], "Should have used observe_page"
        
        print(f"Agent behavior summary: {summary}")
        
    @pytest.mark.asyncio
    async def test_agent_uses_observe_page_after_failure(self, real_agent_with_tracking, observe_tracker):
        """Test that the LLM agent uses observe_page after action failures (success=False)."""
        # Task that will likely cause failures (non-existent elements)
        task = "Navigate to https://example.com and click on the 'NonExistentButton' button"
        
        # Execute task with real API calls
        result = await Runner.run(real_agent_with_tracking, task, max_turns=10)
        
        # Analyze the agent's behavior
        summary = observe_tracker.get_summary()
        
        # Verify the agent attempted the task
        assert summary["total_calls"] >= 2, "Should have made multiple attempts"
        
        # Check if there were failures and if agent observed after them
        if summary["failures"] > 0:
            assert summary["followed_failure_strategy"], \
                "Agent should use observe_page after failures (success=False)"
        
        # Verify observe_page was used for error recovery
        assert summary["observe_calls"] >= 1, "Should have called observe_page for error recovery"
        
        print(f"Failure recovery behavior: {summary}")
        
    @pytest.mark.asyncio
    async def test_agent_retry_logic_with_observe_page(self, real_agent_with_tracking, observe_tracker):
        """Test that the LLM agent uses observe_page in retry logic."""
        # Task requiring multiple attempts and observations
        task = "Navigate to https://www.google.com and search for 'testing'"
        
        # Execute task with real API calls
        result = await Runner.run(real_agent_with_tracking, task, max_turns=10)
        
        # Analyze the agent's behavior
        summary = observe_tracker.get_summary()
        
        # Verify comprehensive tool usage
        assert summary["total_calls"] >= 3, "Should have made multiple tool calls"
        assert summary["observe_calls"] >= 1, "Should have used observe_page"
        
        # Check for proper sequencing
        tool_sequence = [call["tool"] for call in observe_tracker.all_tool_calls]
        
        # Should have navigation, observation, and likely typing
        assert "navigate_to" in tool_sequence, "Should navigate"
        assert "observe_page" in tool_sequence, "Should observe"
        
        # If there were page changes, should have observed
        if summary["page_changes"] > 0:
            assert summary["followed_page_change_strategy"], \
                "Should follow page change strategy"
        
        print(f"Retry logic behavior: {summary}")
        print(f"Tool sequence: {tool_sequence}")
        
    @pytest.mark.asyncio
    async def test_agent_complex_workflow_with_observe_page(self, real_agent_with_tracking, observe_tracker):
        """Test complex workflow to verify observe_page strategy in multi-step scenarios."""
        # Complex task requiring multiple page interactions
        task = """
        Navigate to https://example.com, observe the page, then if possible navigate to any 
        link on the page and observe that new page as well.
        """
        
        # Execute task with real API calls
        result = await Runner.run(real_agent_with_tracking, task, max_turns=10)
        
        # Analyze the agent's behavior
        summary = observe_tracker.get_summary()
        
        # Should have multiple observations in complex workflow
        assert summary["observe_calls"] >= 2, "Should observe multiple times in complex workflow"
        assert summary["total_calls"] >= 4, "Should have multiple tool calls"
        
        # Verify strategic observe_page usage
        observe_calls = observe_tracker.observe_calls
        page_changes = observe_tracker.page_changed_events
        
        # Should have observed after page changes
        if len(page_changes) > 0:
            assert summary["followed_page_change_strategy"], \
                "Should observe after page changes in complex workflow"
        
        # Check tool diversity
        tools_used = summary["tools_used"]
        assert len(tools_used) >= 2, "Should use multiple tools"
        assert "observe_page" in tools_used, "Should use observe_page"
        
        print(f"Complex workflow behavior: {summary}")
        print(f"Observe calls: {len(observe_calls)}")
        print(f"Page changes: {len(page_changes)}")


@pytest.mark.integration
@pytest.mark.slow
class TestObservePageStrategyEdgeCases:
    """Test edge cases and specific scenarios for observe_page strategy."""
    
    @pytest.mark.asyncio
    async def test_agent_handles_slow_pages_with_observe(self, real_agent_with_tracking, observe_tracker):
        """Test agent behavior with slow-loading pages."""
        # Task with slow page
        task = "Navigate to https://httpbin.org/delay/2 and observe the page content"
        
        # Execute with real API calls
        result = await Runner.run(real_agent_with_tracking, task, max_turns=10)
        
        # Analyze behavior
        summary = observe_tracker.get_summary()
        
        # Should handle slow pages and still observe
        assert summary["observe_calls"] >= 1, "Should observe even with slow pages"
        assert summary["total_calls"] >= 2, "Should complete navigation and observation"
        
        # Check for proper error handling
        failures = observe_tracker.failure_events
        if len(failures) > 0:
            assert summary["followed_failure_strategy"], \
                "Should handle slow page failures with observe_page"
        
        print(f"Slow page handling: {summary}")
        
    @pytest.mark.asyncio
    async def test_agent_observe_page_instruction_compliance(self, real_agent_with_tracking, observe_tracker):
        """Test that the agent follows observe_page instructions properly."""
        # Explicit task requiring observation
        task = "Navigate to https://example.com and use observe_page to find all interactive elements"
        
        # Execute with real API calls
        result = await Runner.run(real_agent_with_tracking, task, max_turns=10)
        
        # Analyze behavior
        summary = observe_tracker.get_summary()
        
        # Should explicitly follow observe_page instruction
        assert summary["observe_calls"] >= 1, "Should follow explicit observe_page instruction"
        
        # Check observe_page call details
        observe_calls = observe_tracker.observe_calls
        if len(observe_calls) > 0:
            last_observe = observe_calls[-1]
            assert last_observe["result"].action_type == ActionType.OBSERVE
            assert last_observe["result"].success is True
            
        print(f"Explicit instruction compliance: {summary}")
        print(f"Observe calls made: {len(observe_calls)}")


@pytest.mark.integration
@pytest.mark.slow
class TestObservePageStrategyVerification:
    """Verify that the observe_page strategy is properly implemented in the agent."""
    
    @pytest.mark.asyncio
    async def test_agent_instructions_contain_observe_strategy(self, real_agent_with_tracking):
        """Verify that the agent's instructions contain the observe_page strategy."""
        # Check agent instructions
        instructions = real_agent_with_tracking.instructions
        
        # Verify strategy is documented
        assert "observe_page" in instructions, "Instructions should mention observe_page"
        assert "page_changed=True" in instructions, "Should mention page_changed trigger"
        assert "success=False" in instructions, "Should mention failure trigger"
        assert "OBSERVE_PAGE STRATEGY" in instructions, "Should have strategy section"
        
        # Verify retry strategy mentions observe_page
        assert "RETRY STRATEGY" in instructions, "Should have retry strategy"
        assert "use observe_page for fresh data" in instructions, "Should mention observe_page in retry"
        
        print("✅ Agent instructions contain observe_page strategy")
        
    @pytest.mark.asyncio
    async def test_agent_has_observe_page_tool_available(self, real_agent_with_tracking):
        """Verify that the agent has observe_page tool available."""
        # Check agent tools
        tools = real_agent_with_tracking.tools
        tool_names = [tool.name for tool in tools]
        
        # Verify observe_page is available
        assert "observe_page" in tool_names, "Agent should have observe_page tool"
        
        # Verify all expected tools are available
        expected_tools = ["navigate_to", "click_element", "type_text", "observe_page"]
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Agent should have {tool_name} tool"
        
        print(f"✅ Agent has all required tools: {tool_names}")
        
    @pytest.mark.asyncio
    async def test_integration_test_environment_ready(self, test_urls):
        """Verify that the integration test environment is properly set up."""
        # Check test URLs are accessible
        assert "simple" in test_urls, "Should have simple test URL"
        assert "google" in test_urls, "Should have Google test URL"
        
        # Test URL format
        for name, url in test_urls.items():
            assert url.startswith("http"), f"URL {name} should be properly formatted"
        
        print("✅ Integration test environment is ready")
        print(f"Available test URLs: {list(test_urls.keys())}")


# Helper function to run a specific test
async def run_observe_page_integration_test():
    """Helper function to run a specific integration test manually."""
    from tests.integration.conftest import test_urls
    
    # Create test components
    tracker = ObservePageTracker()
    config = AgentConfig(model="gpt-4o-mini", temperature=0.1)
    agent = create_browser_agent(config)
    
    # Run a simple test
    task = "Navigate to https://example.com and observe the page"
    
    result = await Runner.run(agent, task, max_turns=10)
    
    print(f"Test result: {result}")
    print(f"Tracker summary: {tracker.get_summary()}")
    
    return result


if __name__ == "__main__":
    # Run a simple test when called directly
    import asyncio
    asyncio.run(run_observe_page_integration_test()) 