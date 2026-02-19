"""
Click Actions - Handle element clicking
"""

from typing import Dict, Any, Optional
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
import asyncio


class ClickActions:
    """Handles element click actions"""
    
    WAIT_TIMEOUT = 10  # seconds
    
    def __init__(self, driver=None):
        self.driver = driver
        self._ready = driver is not None
    
    def set_driver(self, driver):
        """Set the WebDriver instance"""
        self.driver = driver
        self._ready = driver is not None
    
    def is_ready(self) -> bool:
        """Check if click actions are ready"""
        return self._ready and self.driver is not None
    
    async def click_element(self, selector: str, wait_for_element: bool = True) -> Dict[str, Any]:
        """
        Click on an element
        
        Args:
            selector: CSS selector for target element
            wait_for_element: Wait for element to be clickable
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
            
            logger.info(f"Attempting to click element: {selector}")
            
            # Find element
            if wait_for_element:
                element = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
            else:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            if not element:
                return {
                    "success": False,
                    "action": "click",
                    "message": "Element not found",
                    "selector": selector
                }
            
            # Validate element is clickable
            validation = self.validate_clickable(element)
            if not validation["is_clickable"]:
                return {
                    "success": False,
                    "action": "click",
                    "message": f"Element not clickable: {validation['reason']}",
                    "selector": selector,
                    "validation": validation
                }
            
            # Get element info before clicking
            element_info = self._get_element_info(element)
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            await asyncio.sleep(0.3)  # Brief pause after scroll
            
            # Try to click
            try:
                element.click()
                click_method = "selenium_click"
            except ElementClickInterceptedException:
                # If regular click fails, try JavaScript click
                logger.warning("Regular click intercepted, trying JavaScript click")
                self.driver.execute_script("arguments[0].click();", element)
                click_method = "javascript_click"
            
            logger.info(f"Successfully clicked element: {selector}")
            
            return {
                "success": True,
                "action": "click",
                "message": "Successfully clicked element",
                "selector": selector,
                "element_info": element_info,
                "click_method": click_method
            }
            
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {selector}")
            return {
                "success": False,
                "action": "click",
                "message": "Timeout waiting for element",
                "selector": selector,
                "error": "timeout"
            }
        except ElementNotInteractableException as e:
            logger.error(f"Element not interactable: {selector}")
            return {
                "success": False,
                "action": "click",
                "message": "Element not interactable",
                "selector": selector,
                "error": str(e)
            }
        except WebDriverException as e:
            logger.error(f"WebDriver error during click: {e}")
            return {
                "success": False,
                "action": "click",
                "message": "Click failed",
                "selector": selector,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return {
                "success": False,
                "action": "click",
                "message": "Click failed",
                "selector": selector,
                "error": str(e)
            }
    
    def validate_clickable(self, element) -> Dict[str, Any]:
        """
        Validate if an element is clickable
        
        Args:
            element: WebElement to validate
            
        Returns:
            Validation result dictionary
        """
        try:
            # Check if element is displayed
            if not element.is_displayed():
                return {
                    "is_clickable": False,
                    "reason": "Element not visible"
                }
            
            # Check if element is enabled
            if not element.is_enabled():
                return {
                    "is_clickable": False,
                    "reason": "Element disabled"
                }
            
            # Check if element has size
            size = element.size
            if size["width"] <= 0 or size["height"] <= 0:
                return {
                    "is_clickable": False,
                    "reason": "Element has no size"
                }
            
            # Check if element is in viewport (optional)
            location = element.location
            if location["x"] < 0 or location["y"] < 0:
                return {
                    "is_clickable": True,  # Still clickable, just needs scroll
                    "reason": "Element outside viewport",
                    "needs_scroll": True
                }
            
            return {
                "is_clickable": True,
                "reason": "Element is clickable"
            }
            
        except Exception as e:
            logger.error(f"Error validating element: {e}")
            return {
                "is_clickable": False,
                "reason": f"Validation error: {str(e)}"
            }
    
    async def double_click_element(self, selector: str) -> Dict[str, Any]:
        """
        Double-click on an element
        
        Args:
            selector: CSS selector for target element
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
            
            logger.info(f"Attempting to double-click element: {selector}")
            
            from selenium.webdriver.common.action_chains import ActionChains
            
            element = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            await asyncio.sleep(0.3)
            
            # Double click
            actions = ActionChains(self.driver)
            actions.double_click(element).perform()
            
            logger.info(f"Successfully double-clicked element: {selector}")
            
            return {
                "success": True,
                "action": "double_click",
                "message": "Successfully double-clicked element",
                "selector": selector
            }
            
        except Exception as e:
            logger.error(f"Error double-clicking element: {e}")
            return {
                "success": False,
                "action": "double_click",
                "message": "Double-click failed",
                "selector": selector,
                "error": str(e)
            }
    
    async def right_click_element(self, selector: str) -> Dict[str, Any]:
        """
        Right-click on an element
        
        Args:
            selector: CSS selector for target element
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
            
            logger.info(f"Attempting to right-click element: {selector}")
            
            from selenium.webdriver.common.action_chains import ActionChains
            
            element = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            await asyncio.sleep(0.3)
            
            # Right click
            actions = ActionChains(self.driver)
            actions.context_click(element).perform()
            
            logger.info(f"Successfully right-clicked element: {selector}")
            
            return {
                "success": True,
                "action": "right_click",
                "message": "Successfully right-clicked element",
                "selector": selector
            }
            
        except Exception as e:
            logger.error(f"Error right-clicking element: {e}")
            return {
                "success": False,
                "action": "right_click",
                "message": "Right-click failed",
                "selector": selector,
                "error": str(e)
            }
    
    def _get_element_info(self, element) -> Dict[str, Any]:
        """
        Get information about an element
        
        Args:
            element: WebElement
            
        Returns:
            Element information dictionary
        """
        try:
            return {
                "tag": element.tag_name,
                "text": element.text[:100] if element.text else "",
                "type": element.get_attribute("type"),
                "id": element.get_attribute("id"),
                "class": element.get_attribute("class"),
                "href": element.get_attribute("href"),
                "aria_label": element.get_attribute("aria-label"),
                "location": element.location,
                "size": element.size
            }
        except Exception as e:
            logger.warning(f"Error getting element info: {e}")
            return {}
