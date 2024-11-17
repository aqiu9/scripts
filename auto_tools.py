import time
from typing import Optional, Tuple, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyautogui
import requests
import numpy as np
import cv2
import ddddocr
from selenium.webdriver.chrome.options import Options

# ========== 浏览器控制 ==========
def start_browser(headless: bool = False, blocked_urls: Optional[list] = None, download_path: str = "downloads") -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-dev-shm-usage')
    prefs = {"download.default_directory": download_path}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    if blocked_urls:
        driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": blocked_urls})
        driver.execute_cdp_cmd("Network.enable", {})
    return driver

def quit_browser(driver: webdriver.Chrome):
    """关闭浏览器"""
    if driver:
        driver.quit()

# ========== 装饰器 ==========
def execution_time_decorator(func):
    """用于装饰器，计算函数执行时间"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        print(f"Execution time: {time.time() - start_time:.2f}s")
        return result
    return wrapper

def retry_on_exception(max_retries: int = 3):
    """重试装饰器，处理常见的瞬时错误"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(1)
            raise RuntimeError("Max retries exceeded")
        return wrapper
    return decorator

# ========== 页面元素提取 ==========
@retry_on_exception()
def find_element_text(driver: webdriver.Chrome, selector: str, by: By = By.CSS_SELECTOR) -> str:
    """根据选择器找到元素文本"""
    return driver.find_element(by, selector).text

@retry_on_exception()
def find_elements_attribute(driver: webdriver.Chrome, selector: str, attribute: str, by: By = By.CSS_SELECTOR) -> list:
    """获取多个元素的属性值"""
    elements = driver.find_elements(by, selector)
    return [element.get_attribute(attribute) for element in elements]

def get_video_durations(driver: webdriver.Chrome, selector: str = "video") -> list:
    """提取页面视频的持续时长"""
    videos = driver.find_elements(By.CSS_SELECTOR, selector)
    return [video.get_attribute("duration") for video in videos]

# ========== 图片识别与点击 ==========
def locate_image(image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
    """在屏幕上定位图像位置"""
    location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
    return location

def click_image(image_path: str, confidence: float = 0.8, wait: float = 0.5) -> bool:
    """点击屏幕上的图像"""
    location = locate_image(image_path, confidence)
    if location:
        pyautogui.click(location)
        time.sleep(wait)
        return True
    return False

def wait_and_click_image(image_path: str, timeout: int = 10, confidence: float = 0.8) -> bool:
    """等待图像出现在屏幕上并点击"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if click_image(image_path, confidence):
            return True
        time.sleep(0.5)
    return False

# ========== 滚动与页面操作 ==========
def scroll_to_bottom(driver: webdriver.Chrome, delay: int = 1, max_attempts: int = 5):
    """滚动页面到底部"""
    for _ in range(max_attempts):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

def click_element(driver: webdriver.Chrome, selector: str, by: By = By.CSS_SELECTOR):
    """点击页面元素"""
    element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((by, selector))
    )
    element.click()

def switch_to_new_tab(driver: webdriver.Chrome):
    """切换到新打开的标签页"""
    driver.switch_to.window(driver.window_handles[-1])

def close_current_tab(driver: webdriver.Chrome):
    """关闭当前标签页"""
    driver.close()
    driver.switch_to.window(driver.window_handles[-1])

# ========== 验证码处理 ==========
def adjust_contrast(img: np.ndarray, contrast: float = 0.8, threshold: float = 0.5) -> np.ndarray:
    """调整验证码图像的对比度"""
    img = img.astype(float)
    img_out = img + (img - threshold * 255.0) * ((1 / (1 - contrast)) - 1) if contrast >= 0 else img + (img - threshold * 255.0) * contrast
    return np.clip(img_out, 0, 255).astype(np.uint8)

def process_captcha_from_url(url: str, contrast: float = 0.8, threshold: float = 0.5) -> str:
    """从URL下载并处理验证码"""
    response = requests.get(url)
    img = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
    img = adjust_contrast(img, contrast, threshold)
    
    ocr = ddddocr.DdddOcr(show_ad=False)
    result = ocr.classification(cv2.imencode(".png", img)[1].tobytes())
    return result

# ========== Session管理 ==========
def login_with_session(login_url: str, username: str, password: str, headers: Optional[Dict[str, str]] = None, csrf_selector: Optional[str] = None, csrf_token: Optional[str] = None) -> Optional[requests.Session]:
    """使用requests Session模拟登录并返回会话对象"""
    session = requests.Session()
    
    headers = headers or {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    response = session.get(login_url, headers=headers)
    if response.status_code != 200:
        print("Failed to load login page")
        return None

    if csrf_selector and not csrf_token:
        csrf_token = extract_csrf_token(response.text, csrf_selector)

    payload = {
        "username": username,
        "password": password,
        "csrf_token": csrf_token
    }
    response = session.post(login_url, data=payload, headers=headers)

    if response.status_code == 200 and "login_success" in response.text:
        print("Login successful")
        return session
    else:
        print("Login failed")
        return None

def extract_csrf_token(page_content: str, selector: str) -> str:
    """解析页面内容提取csrf token"""
    # 根据实际页面结构提取csrf_token
    return "123456"  # 示例返回

# ========== Selenium自动化登录 ==========
def login_with_selenium(driver: webdriver.Chrome, login_url: str, username: str, password: str, config: Dict[str, str]) -> bool:
    """使用Selenium自动化登录并返回True或False"""
    driver.get(login_url)

    driver.find_element(By.CSS_SELECTOR, config['username_selector']).send_keys(username)
    driver.find_element(By.CSS_SELECTOR, config['password_selector']).send_keys(password)
    driver.find_element(By.CSS_SELECTOR, config['login_button_selector']).click()

    try:
        WebDriverWait(driver, config.get('wait_timeout', 10)).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config['login_success_selector']))
        )
        print("Login successful")
        return True
    except Exception:
        print("Login failed")
        return False

def get_cookies(driver: webdriver.Chrome) -> dict:
    """获取登录后的Cookies"""
    return {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}

def login_with_captcha(driver: webdriver.Chrome, login_url: str, username: str, password: str, config: Dict[str, str]) -> bool:
    """处理带验证码的登录"""
    driver.get(login_url)

    driver.find_element(By.CSS_SELECTOR, config['username_selector']).send_keys(username)
    driver.find_element(By.CSS_SELECTOR, config['password_selector']).send_keys(password)

    captcha_image = driver.find_element(By.CSS_SELECTOR, config['captcha_image_selector'])
    captcha_image.screenshot("captcha.png")
    captcha_text = ""  # 使用OCR识别验证码

    driver.find_element(By.CSS_SELECTOR, config['captcha_input_selector']).send_keys(captcha_text)
    driver.find_element(By.CSS_SELECTOR, config['login_button_selector']).click()

    try:
        WebDriverWait(driver, config.get('wait_timeout', 10)).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config['login_success_selector']))
        )
        print("Login successful")
        return True
    except Exception:
        print("Login failed")
        return False

# ========== 浏览器初始化 ==========
def initialize_driver(driver_path: str, headless: bool = True) -> webdriver.Chrome:
    """初始化浏览器驱动，支持无头模式"""
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(driver_path, options=options)
    return driver