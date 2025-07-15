import asyncio
from typing import Optional, Callable, Any, Dict, List, Union
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Route, Request, Response
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def configure_browser_headless(args_headless=None, config_headless=None, env_headless=None):
    """
    קובע אם הדפדפן צריך לפעול במצב headless לפי סדר עדיפויות:
    1. פרמטר בשורת הפקודה
    2. הגדרה בקובץ תצורה
    3. משתנה סביבה
    4. ברירת מחדל: False (דפדפן גלוי)
    
    Returns:
        bool: האם לפעול במצב headless
    """
    # 1. בדוק פרמטר שורת פקודה
    if args_headless is not None:
        return args_headless
    
    # 2. בדוק הגדרה בקובץ תצורה
    if config_headless is not None:
        return config_headless
    
    # 3. בדוק משתנה סביבה
    env_setting = os.environ.get('BROWSER_HEADLESS', '').lower()
    if env_setting in ('true', '1', 'yes'):
        return True
    elif env_setting in ('false', '0', 'no'):
        return False
        
    # 4. ברירת מחדל: דפדפן גלוי
    return False

class BrowserController:
    """
    A class to control browser automation using Playwright.
    Allows opening a browser, performing actions, and closing it when done.
    """
    
    def __init__(self, 
                 browser_type: str = "chromium", 
                 headless: bool = None,
                 slow_mo: int = 0,
                 timeout: int = 30000):
        """
        Initialize the browser controller with configuration options.
        
        Args:
            browser_type: Type of browser to use - "chromium", "firefox", or "webkit"
            headless: Whether to run browser in headless mode
            slow_mo: Slow down operations by specified milliseconds
            timeout: Default timeout for operations in milliseconds
        """
        self.browser_type = browser_type
        self.headless = configure_browser_headless(headless)
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def start(self, device_viewport: Optional[Dict[str, Any]] = None) -> Page:
        """
        Start the browser and open a page.
        
        Args:
            device_viewport: Optional dictionary with viewport settings
                             e.g. {"width": 1280, "height": 720}
        
        Returns:
            Playwright Page object
        """
        try:
            logger.info(f"Starting {self.browser_type} browser")
            self.playwright = await async_playwright().start()
            
            # Select browser type
            if self.browser_type == "chromium":
                browser_instance = self.playwright.chromium
            elif self.browser_type == "firefox":
                browser_instance = self.playwright.firefox
            elif self.browser_type == "webkit":
                browser_instance = self.playwright.webkit
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
            # Launch browser with specified options
            self.browser = await browser_instance.launch(
                headless=self.headless,
                slow_mo=self.slow_mo
            )
            
            # Create browser context with viewport if specified
            context_options = {}
            if device_viewport:
                context_options.update(viewport=device_viewport)
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.timeout)
            
            logger.info(f"Browser started successfully")
            return self.page
            
        except Exception as e:
            logger.error(f"Failed to start browser: {str(e)}")
            await self.close()
            raise
    
    async def navigate(self, url: str) -> None:
        """
        Navigate to a specific URL.
        
        Args:
            url: The URL to navigate to
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            logger.info(f"Navigating to {url}")
            await self.page.goto(url, wait_until="networkidle")
            logger.info(f"Navigation complete")
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            raise
    
    async def run_actions(self, action_func: Callable[[Page], Any]) -> Any:
        """
        Run custom actions on the page.
        
        Args:
            action_func: A callable that takes a Page object and performs actions
        
        Returns:
            The return value of the action_func
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            return await action_func(self.page)
        except Exception as e:
            logger.error(f"Action execution failed: {str(e)}")
            raise
    
    async def take_screenshot(self, path: str) -> None:
        """
        Take a screenshot of the current page.
        
        Args:
            path: Path where to save the screenshot
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            logger.info(f"Taking screenshot to {path}")
            await self.page.screenshot(path=path, full_page=True)
            logger.info(f"Screenshot saved to {path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            raise
    
    async def close(self) -> None:
        """
        Close the browser and clean up resources.
        """
        logger.info("Closing browser")
        
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error during browser closure: {str(e)}")
            raise

async def run_browser_test(url: str, test_function: Optional[Callable[[Page], Any]] = None) -> None:
    """
    Helper function to run a complete browser test.
    It handles starting browser, running test function and closing browser.
    
    Args:
        url: URL to navigate to
        test_function: Optional function to run with the page as argument
    """
    controller = BrowserController(headless=None)
    
    try:
        await controller.start()
        await controller.navigate(url)
        
        if test_function:
            await controller.run_actions(test_function)
            
        # Default 2-second wait to see the result before closing
        await asyncio.sleep(2)
    finally:
        await controller.close()

# Example usage
async def example_test():
    """Example of how to use the BrowserController"""
    
    # Define a test function that will receive the page object
    async def test_actions(page: Page):
        # Get page title
        title = await page.title()
        print(f"Page title: {title}")
        
        # Click a button (if it exists)
        try:
            button = page.locator("text=Accept")
            if await button.count() > 0:
                await button.click()
                print("Clicked 'Accept' button")
        except Exception as e:
            print(f"Button interaction failed: {e}")
        
        # Take screenshot
        await page.screenshot(path="example_screenshot.png")
    
    # Run the test with our defined actions
    await run_browser_test("https://www.example.com", test_actions)

async def open_browser_explicitly():
    """פותח דפדפן באופן יזום כשניתן לראות אותו"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # מוודא שהדפדפן נפתח באופן גלוי עם חלון בגודל סביר
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        await page.goto("https://example.com")
        
        # השהייה כדי לראות את הדפדפן לפני סגירה
        await asyncio.sleep(10)
        
        await browser.close()

# ניתן להריץ את הדוגמאות ישירות מהקובץ
if __name__ == "__main__":
    # הרץ את הדוגמה הרגילה
    asyncio.run(example_test())
    
    # הרץ את הפונקציה שפותחת דפדפן באופן מפורש
    # asyncio.run(open_browser_explicitly())
