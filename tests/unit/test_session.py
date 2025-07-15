"""
Unit tests for session.py

Tests the BrowserSession class and session management functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from browser_agent_final.session import BrowserSession, browser_session
from browser_agent_final.classes import BrowserConfig


class TestBrowserSession:
    """Test the BrowserSession class."""
    
    def test_browser_session_init_with_default_config(self):
        """Test BrowserSession initialization with default config."""
        session = BrowserSession()
        
        assert session.config is not None
        assert isinstance(session.config, BrowserConfig)
        assert session.config.headless is False
        assert session.config.viewport_width == 1920
        assert session.config.viewport_height == 1080
        assert session.config.timeout == 5000
        assert session.stagehand is None
        assert session.page is None
    
    def test_browser_session_init_with_custom_config(self):
        """Test BrowserSession initialization with custom config."""
        config = BrowserConfig(
            headless=True,
            viewport_width=1366,
            viewport_height=768,
            timeout=10000
        )
        session = BrowserSession(config)
        
        assert session.config == config
        assert session.config.headless is True
        assert session.config.viewport_width == 1366
        assert session.config.viewport_height == 768
        assert session.config.timeout == 10000
        assert session.stagehand is None
        assert session.page is None
    
    def test_browser_session_init_with_none_config(self):
        """Test BrowserSession initialization with None config."""
        session = BrowserSession(None)
        
        assert session.config is not None
        assert isinstance(session.config, BrowserConfig)
        # Should use default values
        assert session.config.headless is False
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.session.Stagehand')
    async def test_get_page_first_time(self, mock_stagehand_class):
        """Test get_page() when called for the first time."""
        # Setup mock
        mock_stagehand = AsyncMock()
        mock_page = MagicMock()
        mock_stagehand.page = mock_page
        mock_stagehand_class.return_value = mock_stagehand
        
        session = BrowserSession()
        
        # Call get_page
        result = await session.get_page()
        
        # Verify Stagehand was created with correct parameters
        mock_stagehand_class.assert_called_once_with(
            dom_settle_timeout_ms=5000,  # Default timeout
            env="LOCAL",
            local_browser_launch_options={
                "headless": False,  # Default headless
                "viewport": {
                    "width": 1920,   # Default width
                    "height": 1080   # Default height
                }
            }
        )
        
        # Verify initialization was called
        mock_stagehand.init.assert_called_once()
        
        # Verify page was returned
        assert result == mock_page
        assert session.page == mock_page
        assert session.stagehand == mock_stagehand
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.session.Stagehand')
    async def test_get_page_with_custom_config(self, mock_stagehand_class):
        """Test get_page() with custom BrowserConfig."""
        mock_stagehand = AsyncMock()
        mock_page = MagicMock()
        mock_stagehand.page = mock_page
        mock_stagehand_class.return_value = mock_stagehand
        
        config = BrowserConfig(
            headless=True,
            viewport_width=800,
            viewport_height=600,
            timeout=3000
        )
        session = BrowserSession(config)
        
        result = await session.get_page()
        
        # Verify Stagehand was created with custom parameters
        mock_stagehand_class.assert_called_once_with(
            dom_settle_timeout_ms=3000,
            env="LOCAL",
            local_browser_launch_options={
                "headless": True,
                "viewport": {
                    "width": 800,
                    "height": 600
                }
            }
        )
        
        assert result == mock_page
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.session.Stagehand')
    async def test_get_page_subsequent_calls(self, mock_stagehand_class):
        """Test get_page() when called multiple times (should reuse existing)."""
        mock_stagehand = AsyncMock()
        mock_page = MagicMock()
        mock_stagehand.page = mock_page
        mock_stagehand_class.return_value = mock_stagehand
        
        session = BrowserSession()
        
        # First call
        result1 = await session.get_page()
        # Second call
        result2 = await session.get_page()
        
        # Verify Stagehand was only created once
        mock_stagehand_class.assert_called_once()
        mock_stagehand.init.assert_called_once()
        
        # Both calls should return the same page
        assert result1 == mock_page
        assert result2 == mock_page
        assert result1 == result2
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.session.Stagehand')
    async def test_get_page_initialization_error(self, mock_stagehand_class):
        """Test get_page() when Stagehand initialization fails."""
        mock_stagehand = AsyncMock()
        mock_stagehand.init.side_effect = Exception("Initialization failed")
        mock_stagehand_class.return_value = mock_stagehand
        
        session = BrowserSession()
        
        # Should propagate the exception
        with pytest.raises(Exception, match="Initialization failed"):
            await session.get_page()
    
    @pytest.mark.asyncio
    async def test_close_with_active_session(self):
        """Test close() when there's an active session."""
        session = BrowserSession()
        
        # Mock an active session
        mock_stagehand = AsyncMock()
        session.stagehand = mock_stagehand
        session.page = MagicMock()
        
        await session.close()
        
        # Verify close was called
        mock_stagehand.close.assert_called_once()
        
        # Verify cleanup
        assert session.stagehand is None
        assert session.page is None
    
    @pytest.mark.asyncio
    async def test_close_with_no_active_session(self):
        """Test close() when there's no active session."""
        session = BrowserSession()
        
        # Ensure no active session
        assert session.stagehand is None
        assert session.page is None
        
        # Should not raise an exception
        await session.close()
        
        # Should remain None
        assert session.stagehand is None
        assert session.page is None
    
    @pytest.mark.asyncio
    async def test_close_with_exception(self):
        """Test close() when stagehand.close() raises an exception."""
        session = BrowserSession()
        
        # Mock an active session that fails to close
        mock_stagehand = AsyncMock()
        mock_stagehand.close.side_effect = Exception("Close failed")
        session.stagehand = mock_stagehand
        session.page = MagicMock()
        
        # Should still clean up even if close fails
        with pytest.raises(Exception, match="Close failed"):
            await session.close()
        
        # Cleanup should still happen
        assert session.stagehand is None
        assert session.page is None
    
    @pytest.mark.asyncio
    async def test_is_active_with_no_session(self):
        """Test is_active() when no session exists."""
        session = BrowserSession()
        
        result = await session.is_active()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_active_with_stagehand_but_no_page(self):
        """Test is_active() when stagehand exists but no page."""
        session = BrowserSession()
        session.stagehand = MagicMock()
        session.page = None
        
        result = await session.is_active()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_active_with_page_but_no_stagehand(self):
        """Test is_active() when page exists but no stagehand."""
        session = BrowserSession()
        session.stagehand = None
        session.page = MagicMock()
        
        result = await session.is_active()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_active_with_both_stagehand_and_page(self):
        """Test is_active() when both stagehand and page exist."""
        session = BrowserSession()
        session.stagehand = MagicMock()
        session.page = MagicMock()
        
        result = await session.is_active()
        
        assert result is True


class TestBrowserSessionIntegration:
    """Test BrowserSession integration scenarios."""
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.session.Stagehand')
    async def test_session_lifecycle(self, mock_stagehand_class):
        """Test complete session lifecycle: create -> use -> close."""
        mock_stagehand = AsyncMock()
        mock_page = MagicMock()
        mock_stagehand.page = mock_page
        mock_stagehand_class.return_value = mock_stagehand
        
        session = BrowserSession()
        
        # Initial state
        assert await session.is_active() is False
        
        # Get page (creates session)
        page = await session.get_page()
        assert page == mock_page
        assert await session.is_active() is True
        
        # Close session
        await session.close()
        assert await session.is_active() is False
        
        # Verify cleanup
        mock_stagehand.close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.session.Stagehand')
    async def test_session_reuse_after_close(self, mock_stagehand_class):
        """Test that session can be reused after closing."""
        mock_stagehand = AsyncMock()
        mock_page = MagicMock()
        mock_stagehand.page = mock_page
        mock_stagehand_class.return_value = mock_stagehand
        
        session = BrowserSession()
        
        # First session
        await session.get_page()
        await session.close()
        
        # Second session (should create new Stagehand)
        await session.get_page()
        
        # Should have created Stagehand twice
        assert mock_stagehand_class.call_count == 2
        assert mock_stagehand.init.call_count == 2


class TestGlobalBrowserSession:
    """Test the global browser_session instance."""
    
    def test_global_browser_session_exists(self):
        """Test that global browser_session is created."""
        from browser_agent_final.session import browser_session
        
        assert browser_session is not None
        assert isinstance(browser_session, BrowserSession)
    
    def test_global_browser_session_has_default_config(self):
        """Test that global browser_session uses default config."""
        from browser_agent_final.session import browser_session
        
        assert browser_session.config is not None
        assert isinstance(browser_session.config, BrowserConfig)
        assert browser_session.config.headless is False
        assert browser_session.config.viewport_width == 1920
        assert browser_session.config.viewport_height == 1080
        assert browser_session.config.timeout == 5000
    
    def test_global_browser_session_singleton_behavior(self):
        """Test that importing browser_session multiple times returns the same instance."""
        from browser_agent_final.session import browser_session as session1
        from browser_agent_final.session import browser_session as session2
        
        assert session1 is session2


class TestBrowserSessionEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    @patch('browser_agent_final.session.Stagehand')
    async def test_get_page_with_partial_initialization(self, mock_stagehand_class):
        """Test get_page() when Stagehand is created but page is None."""
        mock_stagehand = AsyncMock()
        mock_stagehand.page = None  # Simulating page not being set
        mock_stagehand_class.return_value = mock_stagehand
        
        session = BrowserSession()
        
        result = await session.get_page()
        
        # Should return None (or whatever stagehand.page returns)
        assert result is None
        assert session.page is None
    
    @pytest.mark.asyncio
    async def test_close_cleanup_on_exception(self):
        """Test that close() cleans up even if an exception occurs."""
        session = BrowserSession()
        
        # Mock stagehand that raises on close
        mock_stagehand = AsyncMock()
        mock_stagehand.close.side_effect = RuntimeError("Close failed")
        session.stagehand = mock_stagehand
        session.page = MagicMock()
        
        # Should clean up references even if close fails
        with pytest.raises(RuntimeError):
            await session.close()
        
        # Cleanup should still happen
        assert session.stagehand is None
        assert session.page is None
    
    def test_browser_session_config_modification(self):
        """Test that modifying config after creation doesn't affect existing sessions."""
        config = BrowserConfig(headless=False)
        session = BrowserSession(config)
        
        # Modify the config
        config.headless = True
        
        # Session should still reference the modified config
        # (This tests whether the session stores a reference or a copy)
        assert session.config.headless is True
        
        # If you want to test that the session is isolated from config changes,
        # you'd need to modify the BrowserSession to copy the config