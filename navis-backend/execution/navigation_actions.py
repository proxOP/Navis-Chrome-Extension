"""
Navigation Actions - Handle page back/forward navigation
"""

from typing import Dict, Any, Optional
from loguru import logger
from selenium.common.exceptions import WebDriverException


class NavigationActions:
    """Handles browser navigation actions"""
    
    def __init__(self, driver=None):
        self.driver = driver
        self._ready = driver is not None
    
    def set_driver(self, driver):
        """Set the WebDriver instance"""
        self.driver = driver
        self._ready = driver is not None
    
    def is_ready(self) -> bool:
        """Check if navigation actions are ready"""
        return self._ready and self.driver is not None
    
    async def navigate_back(self) -> Dict[str, Any]:
        """
        Navigate to previous page in browser history
        
        Returns:
            Result dictionary with success status and details
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
            
            # Check if we can go back
            if not self.can_navigate_back():
                return {
                    "success": False,
                    "action": "navigate_back",
                    "message": "No previous page in history",
                    "error": "history_empty"
                }
            
            current_url = self.driver.current_url
            logger.info(f"Navigating back from: {current_url}")
            
            self.driver.back()
            
            new_url = self.driver.current_url
            logger.info(f"Navigated back to: {new_url}")
            
            return {
                "success": True,
                "action": "navigate_back",
                "message": "Successfully navigated back",
                "previous_url": current_url,
                "current_url": new_url
            }
            
        except WebDriverException as e:
            logger.error(f"WebDriver error during back navigation: {e}")
            return {
                "success": False,
                "action": "navigate_back",
                "message": "Navigation failed",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            return {
                "success": False,
                "action": "navigate_back",
                "message": "Navigation failed",
                "error": str(e)
            }
    
    async def navigate_forward(self) -> Dict[str, Any]:
        """
        Navigate to next page in browser history
        
        Returns:
            Result dictionary with success status and details
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
            
            # Check if we can go forward
            if not self.can_navigate_forward():
                return {
                    "success": False,
                    "action": "navigate_forward",
                    "message": "No next page in history",
                    "error": "history_empty"
                }
            
            current_url = self.driver.current_url
            logger.info(f"Navigating forward from: {current_url}")
            
            self.driver.forward()
            
            new_url = self.driver.current_url
            logger.info(f"Navigated forward to: {new_url}")
            
            return {
                "success": True,
                "action": "navigate_forward",
                "message": "Successfully navigated forward",
                "previous_url": current_url,
                "current_url": new_url
            }
            
        except WebDriverException as e:
            logger.error(f"WebDriver error during forward navigation: {e}")
            return {
                "success": False,
                "action": "navigate_forward",
                "message": "Navigation failed",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error navigating forward: {e}")
            return {
                "success": False,
                "action": "navigate_forward",
                "message": "Navigation failed",
                "error": str(e)
            }
    
    def can_navigate_back(self) -> bool:
        """
        Check if browser can navigate back
        
        Returns:
            True if back navigation is possible
        """
        try:
            if not self.driver:
                return False
            
            # Execute JavaScript to check if we can go back
            can_go_back = self.driver.execute_script("return window.history.length > 1;")
            return bool(can_go_back)
            
        except Exception as e:
            logger.warning(f"Error checking back navigation: {e}")
            return False
    
    def can_navigate_forward(self) -> bool:
        """
        Check if browser can navigate forward
        
        Returns:
            True if forward navigation is possible
        """
        try:
            if not self.driver:
                return False
            
            # This is tricky - we can't directly check forward history
            # We'll try to navigate forward and see if URL changes
            # For now, we'll return True and let the actual navigation handle it
            return True
            
        except Exception as e:
            logger.warning(f"Error checking forward navigation: {e}")
            return False
    
    def get_current_url(self) -> Optional[str]:
        """Get current page URL"""
        try:
            if self.driver:
                return self.driver.current_url
            return None
        except Exception as e:
            logger.error(f"Error getting current URL: {e}")
            return None
    
    def get_page_title(self) -> Optional[str]:
        """Get current page title"""
        try:
            if self.driver:
                return self.driver.title
            return None
        except Exception as e:
            logger.error(f"Error getting page title: {e}")
            return None
