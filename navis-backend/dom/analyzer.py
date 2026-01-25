"""
DOM Analyzer - Analyzes web page structure using Selenium
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, List, Any
from loguru import logger
import time

class DOMAnalyzer:
    def __init__(self):
        self.driver = None
        self._ready = True
        self.setup_driver()
        
    def is_ready(self) -> bool:
        """Check if DOM analyzer is ready"""
        return self._ready and self.driver is not None
    
    def setup_driver(self):
        """Initialize Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            self._ready = False
    
    async def analyze_page(self, url: str) -> Dict[str, Any]:
        """
        Analyze a web page and extract structure
        
        Args:
            url: URL to analyze
            
        Returns:
            Page analysis dictionary
        """
        try:
            if not self.driver:
                raise ValueError("WebDriver not initialized")
                
            logger.info(f"Analyzing page: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            analysis = {
                "url": url,
                "title": self.driver.title,
                "structure": self.extract_page_structure(),
                "interactive_elements": self.find_interactive_elements(),
                "forms": self.analyze_forms(),
                "navigation": self.find_navigation_elements(),
                "landmarks": self.find_landmarks(),
                "accessibility": self.extract_accessibility_info()
            }
            
            logger.info(f"Page analysis completed for {url}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing page {url}: {e}")
            raise ValueError(f"Page analysis failed: {str(e)}")
    
    def extract_page_structure(self) -> Dict[str, Any]:
        """Extract basic page structure"""
        try:
            structure = {
                "title": self.driver.title,
                "url": self.driver.current_url,
                "has_header": len(self.driver.find_elements(By.TAG_NAME, "header")) > 0,
                "has_nav": len(self.driver.find_elements(By.TAG_NAME, "nav")) > 0,
                "has_main": len(self.driver.find_elements(By.TAG_NAME, "main")) > 0,
                "has_footer": len(self.driver.find_elements(By.TAG_NAME, "footer")) > 0,
                "heading_count": len(self.driver.find_elements(By.CSS_SELECTOR, "h1,h2,h3,h4,h5,h6")),
                "link_count": len(self.driver.find_elements(By.TAG_NAME, "a")),
                "image_count": len(self.driver.find_elements(By.TAG_NAME, "img"))
            }
            return structure
        except Exception as e:
            logger.error(f"Error extracting page structure: {e}")
            return {}
    
    def find_interactive_elements(self) -> List[Dict[str, Any]]:
        """Find all interactive elements on the page"""
        elements = []
        
        try:
            # Define selectors for interactive elements
            selectors = [
                'a[href]:not([href="#"])',
                'button:not([disabled])',
                'input[type="submit"]:not([disabled])',
                'input[type="button"]:not([disabled])',
                '[role="button"]:not([aria-disabled="true"])',
                'select:not([disabled])',
                'textarea:not([disabled])',
                'input:not([type="hidden"]):not([disabled])'
            ]
            
            for selector in selectors:
                web_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for i, element in enumerate(web_elements):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            element_info = {
                                "id": f"{selector.split('[')[0]}_{i}",
                                "tag": element.tag_name,
                                "type": element.get_attribute("type") or "unknown",
                                "text": element.text.strip()[:100],  # Limit text length
                                "aria_label": element.get_attribute("aria-label"),
                                "title": element.get_attribute("title"),
                                "href": element.get_attribute("href"),
                                "class": element.get_attribute("class"),
                                "role": element.get_attribute("role"),
                                "selector": self.generate_selector(element),
                                "position": {
                                    "x": element.location["x"],
                                    "y": element.location["y"]
                                },
                                "size": {
                                    "width": element.size["width"],
                                    "height": element.size["height"]
                                }
                            }
                            elements.append(element_info)
                    except Exception as e:
                        logger.warning(f"Error processing element: {e}")
                        continue
            
            logger.info(f"Found {len(elements)} interactive elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error finding interactive elements: {e}")
            return []
    
    def analyze_forms(self) -> List[Dict[str, Any]]:
        """Analyze forms on the page"""
        forms = []
        
        try:
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            
            for i, form in enumerate(form_elements):
                form_info = {
                    "id": f"form_{i}",
                    "action": form.get_attribute("action"),
                    "method": form.get_attribute("method") or "GET",
                    "fields": []
                }
                
                # Find form fields
                fields = form.find_elements(By.CSS_SELECTOR, "input, select, textarea")
                for j, field in enumerate(fields):
                    if field.is_displayed():
                        field_info = {
                            "id": f"field_{i}_{j}",
                            "name": field.get_attribute("name"),
                            "type": field.get_attribute("type") or "text",
                            "placeholder": field.get_attribute("placeholder"),
                            "required": field.get_attribute("required") is not None,
                            "label": self.find_field_label(field)
                        }
                        form_info["fields"].append(field_info)
                
                forms.append(form_info)
            
            return forms
            
        except Exception as e:
            logger.error(f"Error analyzing forms: {e}")
            return []
    
    def find_navigation_elements(self) -> List[Dict[str, Any]]:
        """Find navigation elements"""
        nav_elements = []
        
        try:
            # Look for navigation containers
            nav_containers = self.driver.find_elements(By.CSS_SELECTOR, "nav, [role='navigation']")
            
            for i, nav in enumerate(nav_containers):
                links = nav.find_elements(By.TAG_NAME, "a")
                nav_info = {
                    "id": f"nav_{i}",
                    "type": "navigation",
                    "links": [
                        {
                            "text": link.text.strip(),
                            "href": link.get_attribute("href"),
                            "selector": self.generate_selector(link)
                        }
                        for link in links if link.is_displayed() and link.text.strip()
                    ]
                }
                nav_elements.append(nav_info)
            
            return nav_elements
            
        except Exception as e:
            logger.error(f"Error finding navigation elements: {e}")
            return []
    
    def find_landmarks(self) -> List[Dict[str, Any]]:
        """Find ARIA landmarks and semantic elements"""
        landmarks = []
        
        try:
            landmark_selectors = [
                'header, [role="banner"]',
                'nav, [role="navigation"]', 
                'main, [role="main"]',
                'aside, [role="complementary"]',
                'footer, [role="contentinfo"]',
                '[role="search"]'
            ]
            
            for selector in landmark_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        landmarks.append({
                            "type": element.get_attribute("role") or element.tag_name,
                            "text": element.text.strip()[:200],
                            "selector": self.generate_selector(element)
                        })
            
            return landmarks
            
        except Exception as e:
            logger.error(f"Error finding landmarks: {e}")
            return []
    
    def extract_accessibility_info(self) -> Dict[str, Any]:
        """Extract accessibility information"""
        try:
            accessibility = {
                "has_skip_links": len(self.driver.find_elements(By.CSS_SELECTOR, 'a[href^="#"]')) > 0,
                "aria_labels_count": len(self.driver.find_elements(By.CSS_SELECTOR, '[aria-label]')),
                "headings_structure": self.analyze_heading_structure(),
                "alt_text_coverage": self.check_alt_text_coverage()
            }
            return accessibility
        except Exception as e:
            logger.error(f"Error extracting accessibility info: {e}")
            return {}
    
    def analyze_heading_structure(self) -> List[Dict[str, str]]:
        """Analyze heading structure"""
        headings = []
        try:
            heading_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1,h2,h3,h4,h5,h6")
            for heading in heading_elements:
                if heading.is_displayed():
                    headings.append({
                        "level": heading.tag_name,
                        "text": heading.text.strip()
                    })
            return headings
        except Exception as e:
            logger.error(f"Error analyzing heading structure: {e}")
            return []
    
    def check_alt_text_coverage(self) -> Dict[str, int]:
        """Check alt text coverage for images"""
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            total_images = len(images)
            images_with_alt = len([img for img in images if img.get_attribute("alt")])
            
            return {
                "total_images": total_images,
                "images_with_alt": images_with_alt,
                "coverage_percentage": (images_with_alt / total_images * 100) if total_images > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error checking alt text coverage: {e}")
            return {"total_images": 0, "images_with_alt": 0, "coverage_percentage": 0}
    
    def generate_selector(self, element) -> str:
        """Generate a CSS selector for an element"""
        try:
            # Try ID first
            element_id = element.get_attribute("id")
            if element_id:
                return f"#{element_id}"
            
            # Try unique class combination
            classes = element.get_attribute("class")
            if classes:
                class_selector = "." + ".".join(classes.split())
                # Check if this selector is unique
                matching_elements = self.driver.find_elements(By.CSS_SELECTOR, class_selector)
                if len(matching_elements) == 1:
                    return class_selector
            
            # Fall back to tag name with position
            tag = element.tag_name
            siblings = self.driver.find_elements(By.TAG_NAME, tag)
            if len(siblings) > 1:
                index = siblings.index(element) + 1
                return f"{tag}:nth-of-type({index})"
            
            return tag
            
        except Exception as e:
            logger.warning(f"Error generating selector: {e}")
            return element.tag_name
    
    def find_field_label(self, field) -> str:
        """Find label for a form field"""
        try:
            # Check for explicit label
            field_id = field.get_attribute("id")
            if field_id:
                labels = self.driver.find_elements(By.CSS_SELECTOR, f'label[for="{field_id}"]')
                if labels:
                    return labels[0].text.strip()
            
            # Check for wrapping label
            parent = field.find_element(By.XPATH, "..")
            if parent.tag_name.lower() == "label":
                return parent.text.strip()
            
            # Check for placeholder
            placeholder = field.get_attribute("placeholder")
            if placeholder:
                return placeholder
            
            return ""
            
        except Exception as e:
            return ""
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")