"""
Browser session management.

This module handles the Stagehand browser session lifecycle.
"""

import os
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
                modelName="openai/gpt-4o-mini",  
                modelClientOptions={
                    "apiKey": os.environ.get("OPENAI_API_KEY")
                },
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
            try:
                await self.stagehand.close()
            finally:
                # Always clean up, even if close() fails
                self.stagehand = None
                self.page = None
        else:
            # No stagehand to close, just ensure cleanup
            self.stagehand = None
            self.page = None
    
    async def is_active(self) -> bool:
        """Check if the browser session is active."""
        return self.stagehand is not None and self.page is not None


# Global browser session instance
browser_session = BrowserSession()
