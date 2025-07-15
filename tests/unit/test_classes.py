"""
Enhanced unit tests for classes.py with comprehensive edge case coverage.
"""

import pytest
from pydantic import ValidationError
import json
from unittest.mock import patch
from browser_agent_final.classes import (
    ActionType, 
    ExecutionAction, 
    BrowserConfig, 
    AgentConfig
)


class TestActionType:
    """Test the ActionType enum with comprehensive coverage."""
    
    def test_action_type_values(self):
        """Test that ActionType has the correct values."""
        assert ActionType.NAVIGATE == "navigate"
        assert ActionType.CLICK == "click"
        assert ActionType.TYPE == "type"
    
    def test_action_type_membership(self):
        """Test ActionType membership."""
        assert "navigate" in ActionType
        assert "click" in ActionType
        assert "type" in ActionType
        assert "invalid" not in ActionType
    
    def test_action_type_iteration(self):
        """Test that we can iterate over ActionType."""
        values = list(ActionType)
        assert len(values) == 3
        assert ActionType.NAVIGATE in values
        assert ActionType.CLICK in values
        assert ActionType.TYPE in values
    
    @pytest.mark.parametrize("action_type", ["navigate", "click", "type"])
    def test_action_type_string_conversion(self, action_type):
        """Test ActionType string conversion."""
        enum_value = ActionType(action_type)
        
        # Test that the enum value matches the string
        assert enum_value.value == action_type
        
        # Test that string representation includes the enum name
        assert str(enum_value) == f"ActionType.{action_type.upper()}"
        
        # Test that the enum can be created from the string
        assert ActionType(action_type) == enum_value


class TestExecutionAction:
    """Test the ExecutionAction model with comprehensive validation."""
    
    def test_execution_action_required_fields(self):
        """Test ExecutionAction creation with required fields."""
        action = ExecutionAction(
            success=True,
            action_type="navigate"
        )
        assert action.success is True
        assert action.action_type == "navigate"
        assert action.current_url is None
        assert action.page_title is None
        assert action.instruction is None
        assert action.execution_details is None
        assert action.page_changed is False
        assert action.result_data is None
        assert action.action_taken is None
    
    @pytest.mark.parametrize("action_type", ["navigate", "click", "type"])
    def test_execution_action_all_action_types(self, action_type):
        """Test ExecutionAction with all valid action types."""
        action = ExecutionAction(
            success=True,
            action_type=action_type
        )
        assert action.action_type == action_type
        assert action.success is True
    
    @pytest.mark.parametrize("success_value,expected", [
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        (1, True),
        (0, False),
    ])
    def test_execution_action_success_coercion(self, success_value, expected):
        """Test ExecutionAction success field type coercion."""
        action = ExecutionAction(
            success=success_value,
            action_type="navigate"
        )
        assert action.success is expected
    
    def test_execution_action_field_types_invalid(self):
        """Test ExecutionAction field type validation with invalid values."""
        # Test boolean validation for success - use values that can't be coerced
        with pytest.raises(ValidationError):
            ExecutionAction(success="not_a_boolean", action_type="navigate")
        
        # Test boolean validation for page_changed
        with pytest.raises(ValidationError):
            ExecutionAction(success=True, action_type="navigate", page_changed="not_a_boolean")
    
    def test_execution_action_missing_required_fields(self):
        """Test ExecutionAction validation with missing required fields."""
        # Missing success field
        with pytest.raises(ValidationError) as exc_info:
            ExecutionAction(action_type="navigate")
        assert "success" in str(exc_info.value)
        
        # Missing action_type field
        with pytest.raises(ValidationError) as exc_info:
            ExecutionAction(success=True)
        assert "action_type" in str(exc_info.value)
    
    def test_execution_action_special_characters(self):
        """Test ExecutionAction with special characters in string fields."""
        special_chars_data = {
            "current_url": "https://example.com/path?query=value&special=!@#$%^&*()",
            "page_title": "Test Page with Special Chars: <>\"'&",
            "instruction": "Click the button with text: 'Submit & Continue' <test>",
            "execution_details": "Successfully executed with unicode: 你好世界 🌍",
            "action_taken": "click_element with selector: [data-test='submit-btn']"
        }
        
        action = ExecutionAction(
            success=True,
            action_type="click",
            **special_chars_data
        )
        
        for field, value in special_chars_data.items():
            assert getattr(action, field) == value
    
    def test_execution_action_extremely_long_strings(self):
        """Test ExecutionAction with extremely long string values."""
        long_string = "x" * 10000
        
        action = ExecutionAction(
            success=True,
            action_type="navigate",
            current_url=f"https://example.com/{'a' * 2000}",
            page_title=long_string,
            instruction=long_string,
            execution_details=long_string,
            action_taken=long_string
        )
        
        assert len(action.page_title) == 10000
        assert len(action.instruction) == 10000
        assert len(action.execution_details) == 10000
    
    def test_execution_action_null_validation(self):
        """Test ExecutionAction with null values for optional fields."""
        action = ExecutionAction(
            success=True,
            action_type="navigate",
            current_url=None,
            page_title=None,
            instruction=None,
            execution_details=None,
            result_data=None,
            action_taken=None
        )
        
        # All optional fields should accept None
        assert action.current_url is None
        assert action.page_title is None
        assert action.instruction is None
        assert action.execution_details is None
        assert action.result_data is None
        assert action.action_taken is None
        
    def test_execution_action_complex_result_data(self):
        """Test ExecutionAction with complex result_data structures."""
        complex_data = {
            "elements_found": [
                {"tag": "button", "text": "Submit", "xpath": "//button[1]"},
                {"tag": "input", "type": "text", "id": "email"}
            ],
            "page_info": {
                "url": "https://example.com",
                "load_time": 1.234,
                "elements_count": 45
            },
            "metadata": {
                "timestamp": "2024-01-15T10:30:00Z",
                "user_agent": "Mozilla/5.0...",
                "viewport": {"width": 1920, "height": 1080}
            }
        }
        
        action = ExecutionAction(
            success=True,
            action_type="click",
            result_data=complex_data
        )
        
        assert action.result_data == complex_data
        assert action.result_data["elements_found"][0]["tag"] == "button"
        assert action.result_data["page_info"]["load_time"] == 1.234
    
    def test_execution_action_json_serialization_roundtrip(self):
        """Test ExecutionAction JSON serialization and deserialization."""
        original_action = ExecutionAction(
            success=True,
            action_type="navigate",
            current_url="https://example.com",
            page_title="Test Page",
            page_changed=True,
            result_data={"test": "value"}
        )
        
        # Serialize to JSON
        json_str = original_action.model_dump_json()
        json_data = json.loads(json_str)
        
        # Deserialize back
        restored_action = ExecutionAction.model_validate(json_data)
        
        assert restored_action.success == original_action.success
        assert restored_action.action_type == original_action.action_type
        assert restored_action.current_url == original_action.current_url
        assert restored_action.page_title == original_action.page_title
        assert restored_action.page_changed == original_action.page_changed
        assert restored_action.result_data == original_action.result_data


class TestBrowserConfig:
    """Test the BrowserConfig model with comprehensive validation."""
    
    def test_browser_config_defaults(self):
        """Test BrowserConfig default values."""
        config = BrowserConfig()
        
        assert config.headless is False
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080
        assert config.timeout == 5000
    
    @pytest.mark.parametrize("headless,viewport_width,viewport_height,timeout", [
        (True, 1366, 768, 10000),
        (False, 800, 600, 3000),
        (True, 1920, 1080, 30000),
        (False, 1024, 768, 1000),
    ])
    def test_browser_config_parameterized_values(self, headless, viewport_width, viewport_height, timeout):
        """Test BrowserConfig with various valid combinations."""
        config = BrowserConfig(
            headless=headless,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            timeout=timeout
        )
        
        assert config.headless == headless
        assert config.viewport_width == viewport_width
        assert config.viewport_height == viewport_height
        assert config.timeout == timeout
    
    def test_browser_config_extreme_values(self):
        """Test BrowserConfig with extreme values."""
        # Test very large values
        config = BrowserConfig(
            viewport_width=99999,
            viewport_height=99999,
            timeout=999999
        )
        assert config.viewport_width == 99999
        assert config.viewport_height == 99999
        assert config.timeout == 999999
        
        # Test very small values
        config = BrowserConfig(
            viewport_width=1,
            viewport_height=1,
            timeout=1
        )
        assert config.viewport_width == 1
        assert config.viewport_height == 1
        assert config.timeout == 1
        
        # Test zero values
        config = BrowserConfig(
            viewport_width=0,
            viewport_height=0,
            timeout=0
        )
        assert config.viewport_width == 0
        assert config.viewport_height == 0
        assert config.timeout == 0
        
    def test_browser_config_negative_values(self):
        """Test BrowserConfig with negative values."""
        # Currently allows negative values - test actual behavior
        config = BrowserConfig(
            viewport_width=-1920,
            viewport_height=-1080,
            timeout=-5000
        )
        assert config.viewport_width == -1920
        assert config.viewport_height == -1080
        assert config.timeout == -5000
    
    def test_browser_config_validation_invalid_types(self):
        """Test BrowserConfig field validation with invalid types."""
        # Test invalid types that can't be coerced
        with pytest.raises(ValidationError):
            BrowserConfig(headless="not_a_boolean")
        
        with pytest.raises(ValidationError):
            BrowserConfig(viewport_width="not_a_number")
        
        with pytest.raises(ValidationError):
            BrowserConfig(viewport_height="not_a_number")
        
        with pytest.raises(ValidationError):
            BrowserConfig(timeout="not_a_number")
    
    def test_browser_config_type_coercion(self):
        """Test BrowserConfig type coercion for valid string inputs."""
        config = BrowserConfig(
            headless="true",
            viewport_width="1920",
            viewport_height="1080",
            timeout="5000"
        )
        
        assert config.headless is True
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080
        assert config.timeout == 5000
    
    def test_browser_config_viewport_aspect_ratios(self):
        """Test BrowserConfig with various aspect ratios."""
        aspect_ratios = [
            (1920, 1080),  # 16:9
            (1366, 768),   # 16:9
            (1024, 768),   # 4:3
            (800, 600),    # 4:3
            (1440, 900),   # 16:10
            (2560, 1440),  # 16:9 4K
        ]
        
        for width, height in aspect_ratios:
            config = BrowserConfig(
                viewport_width=width,
                viewport_height=height
            )
            assert config.viewport_width == width
            assert config.viewport_height == height
    
    def test_browser_config_business_logic_validation(self):
        """Test business logic constraints (add custom validators if needed)."""
        # This test documents current behavior
        # If you want to add business logic validation, add custom validators to the model
        
        # Test minimum reasonable viewport size
        config = BrowserConfig(viewport_width=100, viewport_height=100)
        assert config.viewport_width == 100
        assert config.viewport_height == 100
        
        # Test maximum reasonable viewport size
        config = BrowserConfig(viewport_width=7680, viewport_height=4320)  # 8K
        assert config.viewport_width == 7680
        assert config.viewport_height == 4320


class TestAgentConfig:
    """Test the AgentConfig model with comprehensive validation."""
    
    def test_agent_config_defaults(self):
        """Test AgentConfig default values."""
        config = AgentConfig()
        
        assert config.model == "gpt-4o"
        assert config.temperature == 0.3
        assert config.max_turns == 20
    
    @pytest.mark.parametrize("model,temperature,max_turns", [
        ("gpt-4", 0.0, 10),
        ("gpt-3.5-turbo", 0.5, 30),
        ("claude-3-sonnet", 0.7, 50),
        ("gpt-4o", 1.0, 100),
    ])
    def test_agent_config_parameterized_values(self, model, temperature, max_turns):
        """Test AgentConfig with various valid combinations."""
        config = AgentConfig(
            model=model,
            temperature=temperature,
            max_turns=max_turns
        )
        
        assert config.model == model
        assert config.temperature == temperature
        assert config.max_turns == max_turns
    
    def test_agent_config_temperature_bounds(self):
        """Test AgentConfig temperature edge cases and bounds."""
        # Test valid temperature values
        valid_temps = [0.0, 0.1, 0.5, 0.7, 1.0, 1.5, 2.0]
        
        for temp in valid_temps:
            config = AgentConfig(temperature=temp)
            assert config.temperature == temp
        
        # Test extreme temperatures (currently allowed)
        config = AgentConfig(temperature=-1.0)
        assert config.temperature == -1.0
        
        config = AgentConfig(temperature=10.0)
        assert config.temperature == 10.0
    
    def test_agent_config_max_turns_bounds(self):
        """Test AgentConfig max_turns edge cases."""
        # Test various max_turns values
        max_turns_values = [1, 5, 10, 20, 50, 100, 1000]
        
        for max_turns in max_turns_values:
            config = AgentConfig(max_turns=max_turns)
            assert config.max_turns == max_turns
        
        # Test zero and negative values (currently allowed)
        config = AgentConfig(max_turns=0)
        assert config.max_turns == 0
        
        config = AgentConfig(max_turns=-1)
        assert config.max_turns == -1
    
    def test_agent_config_model_names(self):
        """Test AgentConfig with various model names."""
        model_names = [
            "gpt-4",
            "gpt-4o",
            "gpt-3.5-turbo",
            "claude-3-sonnet",
            "claude-3-opus",
            "custom-model-name",
            "model-with-123-numbers",
            "model_with_underscores",
            "model-with-dashes",
        ]
        
        for model in model_names:
            config = AgentConfig(model=model)
            assert config.model == model
    
    def test_agent_config_validation_invalid_types(self):
        """Test AgentConfig field validation with invalid types."""
        # Test invalid types that can't be coerced
        with pytest.raises(ValidationError):
            AgentConfig(model=123)
        
        with pytest.raises(ValidationError):
            AgentConfig(temperature="not_a_number")
        
        with pytest.raises(ValidationError):
            AgentConfig(max_turns="not_a_number")
    
    def test_agent_config_type_coercion(self):
        """Test AgentConfig type coercion for valid string inputs."""
        config = AgentConfig(
            model="gpt-4",
            temperature="0.3",
            max_turns="20"
        )
        
        assert config.model == "gpt-4"
        assert config.temperature == 0.3
        assert config.max_turns == 20
    
    def test_agent_config_business_logic_validation(self):
        """Test business logic constraints for AgentConfig."""
        # Document current behavior and suggest improvements
        
        # Temperature typically should be between 0.0 and 2.0
        # If you want to enforce this, add a custom validator
        config = AgentConfig(temperature=5.0)  # Currently allowed
        assert config.temperature == 5.0
        
        # Max turns should probably be positive
        # If you want to enforce this, add a custom validator
        config = AgentConfig(max_turns=-10)  # Currently allowed
        assert config.max_turns == -10
    
    def test_agent_config_special_characters_in_model(self):
        """Test AgentConfig with special characters in model name."""
        special_models = [
            "model@version-1.0",
            "model:latest",
            "model/with/slashes",
            "model with spaces",
            "model_with_émojis_🤖"
        ]
        
        for model in special_models:
            config = AgentConfig(model=model)
            assert config.model == model


class TestModelIntegration:
    """Test integration between different models and cross-cutting concerns."""
    
    def test_execution_action_with_action_type_enum(self):
        """Test ExecutionAction using ActionType enum values."""
        for action_type in ActionType:
            action = ExecutionAction(
            success=True,
                action_type=action_type
        )
        assert action.action_type == action_type.value
    
    def test_model_immutability_behavior(self):
        """Test model mutability behavior."""
        config = AgentConfig()
        
        # Pydantic models are mutable by default
        original_model = config.model
        config.model = "new-model"
        assert config.model == "new-model"
        assert config.model != original_model
        
        # If you want immutability, you'd need to set frozen=True in model config
    
    def test_config_models_with_browser_config(self):
        """Test interaction between different config models."""
        browser_config = BrowserConfig(
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            timeout=10000
        )
        
        agent_config = AgentConfig(
            model="gpt-4",
            temperature=0.5,
            max_turns=30
        )
        
        # Test that configs can coexist and have different properties
        assert browser_config.headless != agent_config.model
        assert browser_config.timeout != agent_config.max_turns
        assert browser_config.viewport_width != agent_config.temperature
    
    def test_json_serialization_consistency(self):
        """Test JSON serialization consistency across models."""
        models = [
            BrowserConfig(),
            AgentConfig(),
            ExecutionAction(success=True, action_type="navigate")
        ]
        
        for model in models:
            # Test serialization doesn't raise errors
            json_str = model.model_dump_json()
            assert isinstance(json_str, str)
            
            # Test deserialization works
            json_data = json.loads(json_str)
            assert isinstance(json_data, dict)
            
            # Test round-trip
            restored_model = model.__class__.model_validate(json_data)
            assert restored_model.model_dump() == model.model_dump()
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON input."""
        malformed_json_cases = [
            '{"success": true, "action_type": "navigate",}',  # Trailing comma
            '{"success": true "action_type": "navigate"}',    # Missing comma
            '{"success": true, "action_type": navigate}',     # Missing quotes
            '{success: true, action_type: "navigate"}',      # Missing quotes on keys
        ]
        
        for malformed_json in malformed_json_cases:
            with pytest.raises(json.JSONDecodeError):
                json.loads(malformed_json)
    
    def test_partial_model_updates(self):
        """Test partial model updates and validation."""
        # Test partial updates via dict
        original_config = AgentConfig(model="gpt-4", temperature=0.5, max_turns=20)
        
        # Update only some fields
        update_data = {"temperature": 0.7, "max_turns": 30}
        updated_config = original_config.model_copy(update=update_data)
        
        assert updated_config.model == "gpt-4"  # Unchanged
        assert updated_config.temperature == 0.7  # Updated
        assert updated_config.max_turns == 30  # Updated
        
        # Test that original wasn't modified
        assert original_config.temperature == 0.5
        assert original_config.max_turns == 20


class TestPerformanceAndConcurrency:
    """Test performance characteristics and concurrent access."""
    
    def test_model_creation_performance(self):
        """Test model creation performance with large datasets."""
        import time
        
        # Test creating many models quickly
        start_time = time.time()
        
        configs = []
        for i in range(1000):
            config = AgentConfig(
                model=f"model-{i}",
                temperature=i / 1000.0,
                max_turns=i
            )
            configs.append(config)
        
        end_time = time.time()
        
        # Should create 1000 models in reasonable time (< 1 second)
        assert end_time - start_time < 1.0
        assert len(configs) == 1000
    
    def test_json_serialization_performance(self):
        """Test JSON serialization performance."""
        import time
        
        # Create a complex ExecutionAction
        action = ExecutionAction(
            success=True,
            action_type="navigate",
            current_url="https://example.com",
            page_title="Test Page",
            instruction="Navigate to the test page",
            execution_details="Successfully navigated to test page",
            result_data={"elements": [{"tag": "button", "text": "Click me"} for _ in range(100)]}
        )
        
        start_time = time.time()
        
        # Serialize 100 times
        for _ in range(100):
            json_str = action.model_dump_json()
        
        end_time = time.time()
        
        # Should serialize quickly
        assert end_time - start_time < 0.5
        assert len(json_str) > 0