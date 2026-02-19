"""
Scroll Actions - Handle page scrolling
"""

from typing import Dict, Any, Optional
from loguru import logger
from selenium.common.exceptions import WebDriverException
import asyncio


class ScrollActions:
    """Handles page scrolling actions"""
    
    # Default scroll amounts (in pixels)
    DEFAULT_SCROLL_AMOUNT = 500
    SMOOTH_SCROLL_DURATION = 500  # milliseconds
    
    def __init__(self, driver=None):
        self.driver = driver
        self._ready = driver is not None
    
    def set_driver(self, driver):
        """Set the WebDriver instance"""
        self.driver = driver
        self._ready = driver is not None
    
    def is_ready(self) -> bool:
        """Check if scroll actions are ready"""
        return self._ready and self.driver is not None
    
    async def scroll_up(self, amount: Optional[int] = None, smooth: bool = True) -> Dict[str, Any]:
        """
        Scroll page upward
        
        Args:
            amount: Pixels to scroll (default: DEFAULT_SCROLL_AMOUNT)
            smooth: Use smooth scrolling animation
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
            
            scroll_amount = amount or self.DEFAULT_SCROLL_AMOUNT
            
            # Get current scroll position
            current_position = self.get_scroll_position()
            
            # Check if we're already at the top
            if current_position["y"] <= 0:
                return {
                    "success": False,
                    "action": "scroll_up",
                    "message": "Already at top of page",
                    "current_position": current_position
                }
            
            logger.info(f"Scrolling up {scroll_amount}px from position {current_position['y']}")
            
            # Perform scroll
            if smooth:
                scroll_script = f"""
                    window.scrollBy({{
                        top: -{scroll_amount},
                        left: 0,
                        behavior: 'smooth'
                    }});
                """
            else:
                scroll_script = f"window.scrollBy(0, -{scroll_amount});"
            
            self.driver.execute_script(scroll_script)
            
            # Wait for smooth scroll to complete
            if smooth:
                await asyncio.sleep(self.SMOOTH_SCROLL_DURATION / 1000)
            
            # Get new position
            new_position = self.get_scroll_position()
            
            logger.info(f"Scrolled to position {new_position['y']}")
            
            return {
                "success": True,
                "action": "scroll_up",
                "message": "Successfully scrolled up",
                "scroll_amount": scroll_amount,
                "previous_position": current_position,
                "current_position": new_position,
                "pixels_scrolled": current_position["y"] - new_position["y"]
            }
            
        except WebDriverException as e:
            logger.error(f"WebDriver error during scroll up: {e}")
            return {
                "success": False,
                "action": "scroll_up",
                "message": "Scroll failed",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error scrolling up: {e}")
            return {
                "success": False,
                "action": "scroll_up",
                "message": "Scroll failed",
                "error": str(e)
            }
    
    async def scroll_down(self, amount: Optional[int] = None, smooth: bool = True) -> Dict[str, Any]:
        """
        Scroll page downward
        
        Args:
            amount: Pixels to scroll (default: DEFAULT_SCROLL_AMOUNT)
            smooth: Use smooth scrolling animation
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
            
            scroll_amount = amount or self.DEFAULT_SCROLL_AMOUNT
            
            # Get current scroll position
            current_position = self.get_scroll_position()
            max_scroll = self.get_max_scroll_position()
            
            # Check if we're already at the bottom
            if current_position["y"] >= max_scroll["y"]:
                return {
                    "success": False,
                    "action": "scroll_down",
                    "message": "Already at bottom of page",
                    "current_position": current_position,
                    "max_position": max_scroll
                }
            
            logger.info(f"Scrolling down {scroll_amount}px from position {current_position['y']}")
            
            # Perform scroll
            if smooth:
                scroll_script = f"""
                    window.scrollBy({{
                        top: {scroll_amount},
                        left: 0,
                        behavior: 'smooth'
                    }});
                """
            else:
                scroll_script = f"window.scrollBy(0, {scroll_amount});"
            
            self.driver.execute_script(scroll_script)
            
            # Wait for smooth scroll to complete
            if smooth:
                await asyncio.sleep(self.SMOOTH_SCROLL_DURATION / 1000)
            
            # Get new position
            new_position = self.get_scroll_position()
            
            logger.info(f"Scrolled to position {new_position['y']}")
            
            return {
                "success": True,
                "action": "scroll_down",
                "message": "Successfully scrolled down",
                "scroll_amount": scroll_amount,
                "previous_position": current_position,
                "current_position": new_position,
                "pixels_scrolled": new_position["y"] - current_position["y"],
                "at_bottom": new_position["y"] >= max_scroll["y"]
            }
            
        except WebDriverException as e:
            logger.error(f"WebDriver error during scroll down: {e}")
            return {
                "success": False,
                "action": "scroll_down",
                "message": "Scroll failed",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error scrolling down: {e}")
            return {
                "success": False,
                "action": "scroll_down",
                "message": "Scroll failed",
                "error": str(e)
            }
    
    async def scroll_to_element(self, selector: str) -> Dict[str, Any]:
        """
        Scroll to a specific element
        
        Args:
            selector: CSS selector for target element
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
            
            logger.info(f"Scrolling to element: {selector}")
            
            # Find element
            from selenium.webdriver.common.by import By
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            if not element:
                return {
                    "success": False,
                    "action": "scroll_to_element",
                    "message": "Element not found",
                    "selector": selector
                }
            
            # Get current position
            current_position = self.get_scroll_position()
            
            # Scroll to element
            scroll_script = """
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
            """
            self.driver.execute_script(scroll_script, element)
            
            # Wait for smooth scroll
            await asyncio.sleep(self.SMOOTH_SCROLL_DURATION / 1000)
            
            # Get new position
            new_position = self.get_scroll_position()
            
            logger.info(f"Scrolled to element at position {new_position['y']}")
            
            return {
                "success": True,
                "action": "scroll_to_element",
                "message": "Successfully scrolled to element",
                "selector": selector,
                "previous_position": current_position,
                "current_position": new_position
            }
            
        except Exception as e:
            logger.error(f"Error scrolling to element: {e}")
            return {
                "success": False,
                "action": "scroll_to_element",
                "message": "Scroll to element failed",
                "selector": selector,
                "error": str(e)
            }
    
    def get_scroll_position(self) -> Dict[str, int]:
        """
        Get current scroll position
        
        Returns:
            Dictionary with x and y scroll positions
        """
        try:
            if not self.driver:
                return {"x": 0, "y": 0}
            
            position = self.driver.execute_script("""
                return {
                    x: window.pageXOffset || document.documentElement.scrollLeft,
                    y: window.pageYOffset || document.documentElement.scrollTop
                };
            """)
            
            return position
            
        except Exception as e:
            logger.error(f"Error getting scroll position: {e}")
            return {"x": 0, "y": 0}
    
    def get_max_scroll_position(self) -> Dict[str, int]:
        """
        Get maximum scroll position (page dimensions)
        
        Returns:
            Dictionary with max x and y scroll positions
        """
        try:
            if not self.driver:
                return {"x": 0, "y": 0}
            
            max_position = self.driver.execute_script("""
                return {
                    x: Math.max(
                        document.body.scrollWidth,
                        document.documentElement.scrollWidth
                    ) - window.innerWidth,
                    y: Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    ) - window.innerHeight
                };
            """)
            
            return max_position
            
        except Exception as e:
            logger.error(f"Error getting max scroll position: {e}")
            return {"x": 0, "y": 0}
    
    def get_viewport_size(self) -> Dict[str, int]:
        """
        Get viewport dimensions
        
        Returns:
            Dictionary with width and height
        """
        try:
            if not self.driver:
                return {"width": 0, "height": 0}
            
            size = self.driver.execute_script("""
                return {
                    width: window.innerWidth,
                    height: window.innerHeight
                };
            """)
            
            return size
            
        except Exception as e:
            logger.error(f"Error getting viewport size: {e}")
            return {"width": 0, "height": 0}
