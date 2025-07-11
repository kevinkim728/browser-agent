"""
Browser session management.

This module handles the Stagehand browser session lifecycle.
"""

from stagehand import Stagehand
from .classes import BrowserConfig


class BrowserSession:
    """Manages a single browser session using Stagehand."""
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self.stagehand = None
        self.page = None
    
    async def get_page(self):
        """Get or create the browser page."""
        if self.stagehand is None:
            self.stagehand = Stagehand(
                dom_settle_timeout_ms=self.config.timeout,
                env="LOCAL",
                local_browser_launch_options={
                    "headless": self.config.headless,
                    "viewport": {
                        "width": self.config.viewport_width, 
                        "height": self.config.viewport_height
                    }
                } 
            )
            await self.stagehand.init()
            self.page = self.stagehand.page
        return self.page
    
    async def close(self):
        """Close the browser session and cleanup resources."""
        if self.stagehand:
            await self.stagehand.close()
        self.stagehand = None
        self.page = None
    
    async def is_active(self) -> bool:
        """Check if the browser session is active."""
        return self.stagehand is not None and self.page is not None


# Global browser session instance
browser_session = BrowserSession()
