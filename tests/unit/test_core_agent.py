"""
Enhanced unit tests for core_agent.py with comprehensive edge case coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
from browser_agent_final.core_agent import create_browser_agent, browser_agent
from browser_agent_final.classes import AgentConfig
from browser_agent_final.browser_tools import navigate_to, click_element, type_text


class TestCreateBrowserAgent:
    """Test the create_browser_agent function with comprehensive coverage."""
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_with_default_config(self, mock_agent_class):
        """Test creating browser agent with default configuration."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agent = create_browser_agent()
        
        # Verify Agent was called with correct parameters
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        assert call_args[1]["name"] == "browser_automation_agent"
        assert call_args[1]["model"] == "gpt-4o"  # Default from AgentConfig
        assert call_args[1]["tools"] == [navigate_to, click_element, type_text]
        assert "instructions" in call_args[1]
        assert "model_settings" in call_args[1]
        
        # Verify that the function returns the agent instance
        assert agent == mock_agent
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_with_custom_config(self, mock_agent_class):
        """Test creating browser agent with custom configuration."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        custom_config = AgentConfig(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_turns=10
        )
        
        agent = create_browser_agent(custom_config)
        
        # Verify Agent was called with custom parameters
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        assert call_args[1]["name"] == "browser_automation_agent"
        assert call_args[1]["model"] == "gpt-3.5-turbo"
        assert call_args[1]["tools"] == [navigate_to, click_element, type_text]
        
        # Verify model settings
        model_settings = call_args[1]["model_settings"]
        assert model_settings.temperature == 0.7
        
        assert agent == mock_agent
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_with_none_config(self, mock_agent_class):
        """Test creating browser agent with None config (should use defaults)."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        agent = create_browser_agent(None)
        
        # Should use default AgentConfig values
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        
        assert call_args[1]["model"] == "gpt-4o"  # Default
        
        # Verify model settings use default temperature
        model_settings = call_args[1]["model_settings"]
        assert model_settings.temperature == 0.3  # Default
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_instructions_content(self, mock_agent_class):
        """Test that the agent instructions contain expected content."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Check for key instruction components
        assert "browser automation agent" in instructions
        assert "navigate_to" in instructions
        assert "click_element" in instructions
        assert "type_text" in instructions
        assert "AVAILABLE TOOLS" in instructions
        assert "PROMPTING STRUCTURE" in instructions
        assert "RETRY STRATEGY" in instructions
        assert "ExecutionAction" in instructions
    
    @patch('browser_agent_final.core_agent.Agent')
    @patch('browser_agent_final.core_agent.datetime')
    def test_create_browser_agent_date_injection(self, mock_datetime, mock_agent_class):
        """Test that current date is injected into instructions."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # Mock datetime to return a specific date
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2024-01-15"
        mock_datetime.now.return_value = mock_now
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Verify date is in instructions
        assert "2024-01-15" in instructions
        mock_datetime.now.assert_called_once()
        mock_now.strftime.assert_called_once_with("%Y-%m-%d")
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_tools_registration(self, mock_agent_class):
        """Test that all required tools are registered."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        tools = call_args[1]["tools"]
        
        # Verify all tools are present
        assert len(tools) == 3
        assert navigate_to in tools
        assert click_element in tools
        assert type_text in tools
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_model_settings(self, mock_agent_class):
        """Test ModelSettings configuration."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        config = AgentConfig(temperature=0.8)
        create_browser_agent(config)
        
        call_args = mock_agent_class.call_args
        model_settings = call_args[1]["model_settings"]
        
        # Check that ModelSettings is configured correctly
        assert hasattr(model_settings, "temperature")
        assert model_settings.temperature == 0.8


class TestBrowserAgentModule:
    """Test the browser_agent module-level instance."""
    
    def test_browser_agent_instance_exists(self):
        """Test that browser_agent instance is created."""
        assert browser_agent is not None
    
    def test_browser_agent_has_correct_attributes(self):
        """Test that browser_agent has expected attributes."""
        assert hasattr(browser_agent, 'name')
        assert hasattr(browser_agent, 'instructions')
        assert hasattr(browser_agent, 'model')
        assert hasattr(browser_agent, 'tools')
        
        # Test that tools are properly registered
        assert browser_agent.tools is not None
        assert len(browser_agent.tools) == 3
    
    def test_browser_agent_uses_default_config(self):
        """Test that browser_agent uses default configuration values."""
        assert browser_agent.model == "gpt-4o"  # Default from AgentConfig
        
        # Test that instructions contain expected content
        assert "browser automation agent" in browser_agent.instructions
        assert "navigate_to" in browser_agent.instructions
        assert "click_element" in browser_agent.instructions
        assert "type_text" in browser_agent.instructions
    
    def test_browser_agent_singleton_behavior(self):
        """Test that importing browser_agent multiple times returns same instance."""
        from browser_agent_final.core_agent import browser_agent as agent1
        from browser_agent_final.core_agent import browser_agent as agent2
        
        assert agent1 is agent2
    
    def test_browser_agent_default_parameters(self):
        """Test that browser_agent was created with specific default parameters."""
        # Test the actual instance properties
        assert browser_agent.name == "browser_automation_agent"
        assert browser_agent.model == "gpt-4o"
        
        # Test model settings
        assert hasattr(browser_agent, 'model_settings')
        assert browser_agent.model_settings.temperature == 0.3
        
        # Test tools are correct instances (check the tools directly)
        assert len(browser_agent.tools) == 3
        
        # Verify the tools are the expected FunctionTool instances
        assert navigate_to in browser_agent.tools
        assert click_element in browser_agent.tools
        assert type_text in browser_agent.tools
        
        # Verify all tools are FunctionTool instances
        for tool in browser_agent.tools:
            assert tool.__class__.__name__ == 'FunctionTool'
    


class TestAgentInstructions:
    """Test agent instruction generation and content."""
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_instructions_structure(self, mock_agent_class):
        """Test that instructions have proper structure."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Test key sections exist
        sections = [
            "AVAILABLE TOOLS:",
            "PROMPTING STRUCTURE:",
            "RETRY STRATEGY:",
            "Your process:"
        ]
        
        for section in sections:
            assert section in instructions
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_instructions_tool_descriptions(self, mock_agent_class):
        """Test that tool descriptions are present."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Check tool descriptions
        assert "navigate_to - Navigate to any URL" in instructions
        assert "click_element - Click on elements" in instructions
        assert "type_text - Type text into fields" in instructions
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_instructions_execution_analysis(self, mock_agent_class):
        """Test that execution analysis instructions are present."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Check ExecutionAction analysis instructions
        execution_fields = [
            "success: Whether the action worked",
            "action_taken: The action that was taken",
            "execution_details: Specific details about the execution",
            "page_changed: For actions expecting to change the page",
            "result_data: Full returned data by the action"
        ]
        
        for field in execution_fields:
            assert field in instructions
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_instructions_length_and_completeness(self, mock_agent_class):
        """Test that instructions are comprehensive and well-formed."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        create_browser_agent()
        
        call_args = mock_agent_class.call_args
        instructions = call_args[1]["instructions"]
        
        # Test instructions are substantial
        assert len(instructions) > 1000  # Should be comprehensive
        
        # Test no placeholder text remains
        assert "TODO" not in instructions
        assert "PLACEHOLDER" not in instructions
        
        # Test proper formatting
        assert "\n" in instructions  # Multi-line
        assert "**" in instructions  # Bold formatting


class TestAgentConfigurationEdgeCases:
    """Test edge cases and comprehensive error conditions."""
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_with_invalid_config_types(self, mock_agent_class):
        """Test creating agent with various invalid config types."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        invalid_configs = [
            ("string", "invalid_config"),
            ("integer", 123),
            ("float", 45.67),
            ("list", [1, 2, 3]),
            ("dict", {"model": "test"}),
            ("boolean", True),
        ]
        
        for config_type, invalid_config in invalid_configs:
            with pytest.raises(AttributeError) as exc_info:
                create_browser_agent(invalid_config)
            
            # Check that error message is about missing attributes
            error_message = str(exc_info.value)
            assert "object has no attribute" in error_message or "attribute" in error_message
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_preserves_config_isolation(self, mock_agent_class):
        """Test that creating multiple agents doesn't share config."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        config1 = AgentConfig(model="gpt-4", temperature=0.1)
        config2 = AgentConfig(model="gpt-3.5-turbo", temperature=0.9)
        
        agent1 = create_browser_agent(config1)
        agent2 = create_browser_agent(config2)
        
        # Verify both agents were created
        assert mock_agent_class.call_count == 2
        
        # Get the call arguments for both calls
        call1_args = mock_agent_class.call_args_list[0]
        call2_args = mock_agent_class.call_args_list[1]
        
        # Verify different configurations were used
        assert call1_args[1]["model"] == "gpt-4"
        assert call2_args[1]["model"] == "gpt-3.5-turbo"
        
        assert call1_args[1]["model_settings"].temperature == 0.1
        assert call2_args[1]["model_settings"].temperature == 0.9
    
    @patch('browser_agent_final.core_agent.Agent')
    @pytest.mark.parametrize("temperature", [0.0, 0.5, 1.0, 1.5, 2.0])
    def test_create_browser_agent_extreme_temperature_values(self, mock_agent_class, temperature):
        """Test creating agent with extreme temperature values."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        config = AgentConfig(temperature=temperature)
        agent = create_browser_agent(config)
        
        call_args = mock_agent_class.call_args
        model_settings = call_args[1]["model_settings"]
        
        assert model_settings.temperature == temperature
    
    @patch('browser_agent_final.core_agent.Agent')
    @pytest.mark.parametrize("temperature", [-1.0, 5.0, 10.0, 100.0])
    def test_create_browser_agent_invalid_temperature_values(self, mock_agent_class, temperature):
        """Test creating agent with invalid temperature values."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        # Currently AgentConfig allows any temperature - test documents this behavior
        config = AgentConfig(temperature=temperature)
        agent = create_browser_agent(config)
        
        call_args = mock_agent_class.call_args
        model_settings = call_args[1]["model_settings"]
        
        assert model_settings.temperature == temperature
    
    @patch('browser_agent_final.core_agent.Agent')
    @pytest.mark.parametrize("max_turns", [1, 5, 10, 20, 50, 100, 1000])
    def test_create_browser_agent_max_turns_edge_cases(self, mock_agent_class, max_turns):
        """Test creating agent with various max_turns values."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        config = AgentConfig(max_turns=max_turns)
        agent = create_browser_agent(config)
        
        # Verify agent was created successfully
        assert agent == mock_agent
        
        # Verify config was used
        call_args = mock_agent_class.call_args
        assert call_args[1]["model"] == "gpt-4o"  # Default model
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_very_long_model_names(self, mock_agent_class):
        """Test creating agent with very long model names."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        long_model_names = [
            "a" * 100,  # 100 characters
            "model-with-very-long-name-that-exceeds-normal-expectations-and-continues-for-a-very-long-time",
            "model_with_underscores_" * 10,
            "model-with-dashes-" * 10,
            "🤖" * 50,  # Unicode characters
        ]
        
        for model_name in long_model_names:
            config = AgentConfig(model=model_name)
            agent = create_browser_agent(config)
            
            call_args = mock_agent_class.call_args
            assert call_args[1]["model"] == model_name
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_special_characters_in_model(self, mock_agent_class):
        """Test creating agent with special characters in model names."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        special_models = [
            "model@version-1.0",
            "model:latest", 
            "model/with/slashes",
            "model with spaces",
            "model_with_émojis_🤖",
            "model<>\"'&",
            "model;DROP TABLE models;--",  # SQL injection attempt
        ]
        
        for model in special_models:
            config = AgentConfig(model=model)
            agent = create_browser_agent(config)
            
            call_args = mock_agent_class.call_args
            assert call_args[1]["model"] == model
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_boundary_max_turns(self, mock_agent_class):
        """Test creating agent with boundary max_turns values."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        boundary_values = [
            0,      # Zero turns
            -1,     # Negative turns
            -100,   # Very negative
            99999,  # Very large
        ]
        
        for max_turns in boundary_values:
            config = AgentConfig(max_turns=max_turns)
            agent = create_browser_agent(config)
            
            # Should create agent successfully (documents current behavior)
            assert agent == mock_agent
    
    @patch('browser_agent_final.core_agent.Agent')
    def test_create_browser_agent_config_mutation_safety(self, mock_agent_class):
        """Test that modifying config after agent creation doesn't affect agent."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        
        config = AgentConfig(model="original-model", temperature=0.5)
        agent = create_browser_agent(config)
        
        # Get the original call args
        original_call_args = mock_agent_class.call_args
        
        # Modify the config after agent creation
        config.model = "modified-model"
        config.temperature = 0.9
        
        # Verify the agent was created with original values
        assert original_call_args[1]["model"] == "original-model"
        assert original_call_args[1]["model_settings"].temperature == 0.5