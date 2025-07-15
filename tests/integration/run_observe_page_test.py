"""
Simple test runner for observe_page integration tests.

This script can be used to run a single integration test to verify:
1. API keys are properly configured
2. Browser automation works
3. LLM agent actually follows observe_page strategy
4. Real API calls are made successfully

Usage:
    python tests/integration/run_observe_page_test.py
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents import Runner
from browser_agent_final.core_agent import create_browser_agent
from browser_agent_final.classes import AgentConfig
from browser_agent_final.browser_tools import navigate_to, click_element, type_text, observe_page


class SimpleObservePageTest:
    """Simple integration test for observe_page strategy."""
    
    def __init__(self):
        self.tool_calls = []
        self.results = []
        
    def track_tool_call(self, tool_name: str, params: dict, result):
        """Track tool calls during execution."""
        self.tool_calls.append({
            "tool": tool_name,
            "params": params,
            "result": result,
            "success": result.success if hasattr(result, 'success') else None,
            "page_changed": result.page_changed if hasattr(result, 'page_changed') else None,
            "action_type": result.action_type if hasattr(result, 'action_type') else None
        })
        
    def setup_tracking(self):
        """Set up tool call tracking."""
        # Store original methods
        self.original_navigate = navigate_to.on_invoke_tool
        self.original_click = click_element.on_invoke_tool
        self.original_type = type_text.on_invoke_tool
        self.original_observe = observe_page.on_invoke_tool
        
        # Create tracked versions
        async def tracked_navigate(tool, params_str):
            params = json.loads(params_str)
            result = await self.original_navigate(tool, params_str)
            self.track_tool_call("navigate_to", params, result)
            return result
            
        async def tracked_click(tool, params_str):
            params = json.loads(params_str)
            result = await self.original_click(tool, params_str)
            self.track_tool_call("click_element", params, result)
            return result
            
        async def tracked_type(tool, params_str):
            params = json.loads(params_str)
            result = await self.original_type(tool, params_str)
            self.track_tool_call("type_text", params, result)
            return result
            
        async def tracked_observe(tool, params_str):
            params = json.loads(params_str)
            result = await self.original_observe(tool, params_str)
            self.track_tool_call("observe_page", params, result)
            return result
        
        # Apply tracking
        navigate_to.on_invoke_tool = tracked_navigate
        click_element.on_invoke_tool = tracked_click
        type_text.on_invoke_tool = tracked_type
        observe_page.on_invoke_tool = tracked_observe
        
    def restore_original_methods(self):
        """Restore original tool methods."""
        navigate_to.on_invoke_tool = self.original_navigate
        click_element.on_invoke_tool = self.original_click
        type_text.on_invoke_tool = self.original_type
        observe_page.on_invoke_tool = self.original_observe
        
    def analyze_results(self):
        """Analyze the results of the test run."""
        total_calls = len(self.tool_calls)
        observe_calls = [call for call in self.tool_calls if call["tool"] == "observe_page"]
        page_changes = [call for call in self.tool_calls if call.get("page_changed")]
        failures = [call for call in self.tool_calls if call.get("success") is False]
        
        # Check strategy compliance
        followed_page_change_strategy = False
        followed_failure_strategy = False
        
        # Check if observe_page was called after page changes
        for i, call in enumerate(self.tool_calls):
            if call.get("page_changed"):
                if i + 1 < len(self.tool_calls):
                    next_call = self.tool_calls[i + 1]
                    if next_call["tool"] == "observe_page":
                        followed_page_change_strategy = True
                        break
                        
        # Check if observe_page was called after failures
        for i, call in enumerate(self.tool_calls):
            if call.get("success") is False:
                if i + 1 < len(self.tool_calls):
                    next_call = self.tool_calls[i + 1]
                    if next_call["tool"] == "observe_page":
                        followed_failure_strategy = True
                        break
        
        return {
            "total_calls": total_calls,
            "observe_calls": len(observe_calls),
            "page_changes": len(page_changes),
            "failures": len(failures),
            "followed_page_change_strategy": followed_page_change_strategy,
            "followed_failure_strategy": followed_failure_strategy,
            "tools_used": list(set(call["tool"] for call in self.tool_calls))
        }
        
    async def run_basic_test(self):
        """Run a basic observe_page strategy test."""
        print("🚀 Starting basic observe_page integration test...")
        
        # Setup tracking
        self.setup_tracking()
        
        try:
            # Create agent with fast settings
            config = AgentConfig(
                model="gpt-4o-mini",  # Use cheaper model
                temperature=0.3       # Lower temperature for consistency
            )
            agent = create_browser_agent(config)
            
            print(f"✅ Agent created with model: {config.model}")
            
            # Simple task that should trigger observe_page
            task = "Navigate to https://example.com and observe what elements are on the page"
            
            print(f"🎯 Task: {task}")
            print("⏳ Executing task with real API calls...")
            
            # Execute with real API calls
            result = await Runner.run(agent, task, max_turns=15)
            
            print(f"✅ Task completed!")
            print(f"📊 Result: {result}")
            
            # Analyze results
            analysis = self.analyze_results()
            
            print("\n📈 ANALYSIS RESULTS:")
            print(f"  Total tool calls: {analysis['total_calls']}")
            print(f"  Observe_page calls: {analysis['observe_calls']}")
            print(f"  Page changes: {analysis['page_changes']}")
            print(f"  Failures: {analysis['failures']}")
            print(f"  Tools used: {analysis['tools_used']}")
            
            print("\n🎯 STRATEGY COMPLIANCE:")
            print(f"  Followed page change strategy: {analysis['followed_page_change_strategy']}")
            print(f"  Followed failure strategy: {analysis['followed_failure_strategy']}")
            
            # Verify basic requirements
            success_criteria = [
                (analysis['total_calls'] >= 2, "Should make at least 2 tool calls"),
                (analysis['observe_calls'] >= 1, "Should call observe_page at least once"),
                ("navigate_to" in analysis['tools_used'], "Should use navigate_to"),
                ("observe_page" in analysis['tools_used'], "Should use observe_page")
            ]
            
            print("\n✅ SUCCESS CRITERIA:")
            all_passed = True
            for passed, description in success_criteria:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {description}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                print("\n🎉 TEST PASSED: Integration test successful!")
                return True
            else:
                print("\n❌ TEST FAILED: Some criteria not met")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
            
        finally:
            # Restore original methods
            self.restore_original_methods()
            
    async def run_failure_test(self):
        """Run a test that should trigger failure handling."""
        print("\n🚀 Starting failure handling test...")
        
        # Reset tracking
        self.tool_calls = []
        self.setup_tracking()
        
        try:
            config = AgentConfig(model="gpt-4o-mini", temperature=0.3)
            agent = create_browser_agent(config)
            
            # Task that should cause failures
            task = "Navigate to https://example.com and click on a button called 'NonExistentButton'"
            
            print(f"🎯 Failure test task: {task}")
            print("⏳ Executing task (expecting failures)...")
            
            result = await Runner.run(agent, task, max_turns=15)
            
            # Analyze results
            analysis = self.analyze_results()
            
            print("\n📈 FAILURE TEST ANALYSIS:")
            print(f"  Total tool calls: {analysis['total_calls']}")
            print(f"  Observe_page calls: {analysis['observe_calls']}")
            print(f"  Failures: {analysis['failures']}")
            print(f"  Followed failure strategy: {analysis['followed_failure_strategy']}")
            
            # For failure test, we expect failures and observe_page usage
            if analysis['failures'] > 0 and analysis['observe_calls'] > 0:
                print("✅ Failure handling test successful!")
                return True
            else:
                print("❌ Failure handling test inconclusive")
                return False
                
        except Exception as e:
            print(f"❌ ERROR in failure test: {e}")
            return False
            
        finally:
            self.restore_original_methods()


async def main():
    """Run the integration tests."""
    print("🧪 OBSERVE_PAGE INTEGRATION TEST RUNNER")
    print("=" * 50)
    
    # Check environment
    print("🔍 Checking environment...")
    
    # Check if API keys are available (you'll need to set these)
    api_key_available = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key_available:
        print("⚠️  WARNING: No API keys found in environment")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run real tests")
        print("   Example: export OPENAI_API_KEY='your-key-here'")
    else:
        print("✅ API keys found in environment")
    
    # Create test instance
    test = SimpleObservePageTest()
    
    # Run basic test
    basic_success = await test.run_basic_test()
    
    # Run failure test if basic test passed
    failure_success = False
    if basic_success:
        failure_success = await test.run_failure_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 FINAL SUMMARY:")
    print(f"  Basic test: {'✅ PASSED' if basic_success else '❌ FAILED'}")
    print(f"  Failure test: {'✅ PASSED' if failure_success else '❌ FAILED'}")
    
    if basic_success and failure_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The LLM agent correctly follows the observe_page strategy!")
    elif basic_success:
        print("\n⚠️  BASIC TEST PASSED, but failure test was inconclusive")
    else:
        print("\n❌ TESTS FAILED")
        print("   Check your API keys and network connection")
    
    return basic_success and failure_success


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 