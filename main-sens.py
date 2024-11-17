import imagehash
from PIL import Image
from playwright.sync_api import sync_playwright
import pyautogui

def _locate_image(image_path: str, confidence: float = 0.8):
    location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
    return location

def click_image(image_path: str, confidence: float = 0.8) -> bool:
    location = _locate_image(image_path, confidence)
    if location:
        pyautogui.click(location)
        return True
    return False

# 方法 1: 感知哈希 (pHash)
def compare_phash(image_path1, image_path2):
    pil_image1 = Image.open(image_path1)
    pil_image2 = Image.open(image_path2)
    hash1 = imagehash.phash(pil_image1)
    hash2 = imagehash.phash(pil_image2)
    similarity = 1 - (hash1 - hash2) / len(hash1.hash.flatten())
    return similarity

def convert_duration_to_seconds(duration):
    # 补齐成 "hh:mm:ss" 格式，方便处理
    parts = duration.split(":")
    if len(parts) == 2:
        parts.insert(0, "0")  # 在小时位置补0
    hours, minutes, seconds = map(int, parts)
    print(f"Hours: {hours}, Minutes: {minutes}, Seconds: {seconds}")
    return hours * 3600 + minutes * 60 + seconds

def login(page, config, username, password):
    page.goto(config['login_url'], timeout=60*1000)
    page.fill(config['username_selector'], username)
    page.fill(config['password_selector'], password)
    page.click(config['login_button_selector'])
    page.wait_for_selector(config['login_success_selector'])  # 确认登录成功
    print("登陆成功.")

# 转到课程学习页面
def navigate_to_courses(page, config):
    page.click(f"text={config['course_button_text']}")
    page.wait_for_selector(config['card_item_selector'])  # 确认课程页面加载
    print("转到课程页面..")

# 列出本页学习情况
def list_courses(page, config, cur_page_num):
    page.reload()
    # page.click(f"text=最新")
    # print("按最新排序...")
    # page.wait_for_timeout(1e3) 
    switch_to_page_num(page, config, cur_page_num)

    course_elements = page.query_selector_all(config['card_item_selector'])
    unfinished_courses = []
    
    for course in course_elements:
        title = course.query_selector(config['content_area_selector']).inner_text()
        status_elements = course.query_selector_all(config['status_selector'])
        
        is_completed = any("已完成" in status.text_content() for status in status_elements)
        if not is_completed:
            unfinished_courses.append(title)
    
    print("-总课程数量:", len(course_elements))
    print("-未学习课程数量:", len(unfinished_courses))
    print("-未学习课程清单:", unfinished_courses)
    print("-Skip Courses:", config['skip_courses'])
    return list(filter(lambda c: c not in config['skip_courses'], unfinished_courses))

def switch_to_page_num(page, config, to_page_num, from_page_num=1):
    click_times = to_page_num - from_page_num
    for _ in range(click_times):
        page.click(f"text={config['next_page_text']}")
        page.wait_for_selector(config['card_item_selector'])  # 等待新页面加载
        if _ == click_times-1:
            page.wait_for_timeout(1e3)
            page.wait_for_load_state("networkidle") #'是否完成'等状态是异步加载的，只有上一句可能没有加载出数据，只加载了网页框架。
            
def try_click(click_fn, *args):
    try:
        click_fn(*args)
        return True
    except Exception as e:
        print(f"{click_fn.__name__}点击失败: {args}")
        return False

def try_play(page, play_btn_paths, play_element_locators, is_headless):
    if not is_headless:
        # 有头，优先尝试图像定位播放
        for image_path in play_btn_paths:
            if try_click(click_image, image_path):
                print(f"---图像定位播放：{image_path}---")
                return True
    # 尝试元素定位播放
    for loc in play_element_locators:
        if try_click(page.locator(loc).click):
            print("---元素定位播放---")
            return True
    print(f"-模拟播放失败,可能自动播放了..")  # 可能是自动播放了 
    return False

# 学习一个视频
def play_video(page, course_title, config, is_headless):
    with page.context.expect_page() as newpage:
        try:
            page.click(f"text={course_title}")
            video_page = newpage.value
            video_page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"-视频页面打开失败，暂时跳过“{course_title.split()[0]}”。错误信息：{e}")
            return

        # iframe检测
        iframe = None
        if video_page.query_selector("iframe"):
            iframe = video_page.frame_locator("iframe")
        else:
            print(f"-未检测到iframe，直接在页面上定位")
        
        # 有iframe时，视频下面会有一个状态元素
        if iframe:
            try:
                status = iframe.locator(".progress-view-status").inner_text()
                if "已完成" in status:
                    print(f"---课程“{course_title}”状态显示已完成，跳过学习---")
                    video_page.close()
                    return
            except Exception as e:
                print(f"--未找到学习状态，继续学习视频。错误信息：{e}")

        play_btn_paths = ['play.png', 'play1.png', 'play2.png']
        play_element_locators = ['.vjs-big-play-button', '#D209registerMask']
        try_play(iframe if iframe else video_page, play_btn_paths, play_element_locators, is_headless)

        video_page.screenshot(path="after_play.png")
        print(f"-开始学习：“{course_title.split()[0]}”")
        video_page.wait_for_timeout(15e3) # 防止意外，稍微加固
        video_page.screenshot(path="after_play_15s.png")
        similarity = compare_phash("after_play.png", "after_play_5s.png")
        if similarity < 0.95:
            print(f"--15s相似度{similarity}，播放中...")
            try:
                duration = iframe.locator('.vjs-duration-display').inner_text().split()[-1] if iframe else video_page.locator('.vjs-duration-display').inner_text().split()[-1]
                played_duration = iframe.locator('.vjs-current-time-display').inner_text().split()[-1] if iframe else video_page.locator('.vjs-current-time-display').inner_text().split()[-1] 
                left_seconds = convert_duration_to_seconds(duration) - convert_duration_to_seconds(played_duration)
                print(f"--left seconds： {left_seconds}")
                video_page.wait_for_timeout(left_seconds*1e3)  # 等待视频播放完毕
            except:
                print("--Got duration failed, wait 30 mins..")
                video_page.wait_for_timeout(30*60e3)
            print("---学习结束---")
        else:
            print(f"--15s相似度{similarity}，播放失败！")
            
        video_page.close()  # 关闭视频页面

# main loop，翻页和学习
def study_courses(page, config, is_headless):
    cur_page_num = 1
    page_try_times = {}
    while True:
        if (times:=page_try_times.get(cur_page_num, 0)) < 2 and (unfinished_courses:=list_courses(page, config, cur_page_num)):
            page_try_times[cur_page_num] = times + 1
            
            if unfinished_courses:
                for course_title in unfinished_courses:
                    play_video(page, course_title, config, is_headless)
        else:
           switch_to_page_num(page, config, to_page_num=cur_page_num+1, from_page_num=cur_page_num)
           cur_page_num += 1

def main():
    config = {
        'login_url': "https://zhixueyun.com/",
        'username_selector': '#D65username',
        'password_selector': '#D65pword',
        'login_button_selector': '#D65login',
        'login_success_selector': '.app-header-logo',
        'next_page_text': "下一页",
        'course_button_text': "课程",
        'card_item_selector': ".card-item",
        'content_area_selector': ".content-area",
        'status_selector': ".status",
        'duration_display_selector': "span.vjs-duration-display", # 没采用
        'play_button_selector': "#D209registerMask",  # 没采用
        'iframe_selector': "iframe",  # 没采用
        'skip_courses': ['领导性格分析与胜任力提升（一）\n学分: - 学时: - 共2节', '领导性格分析与胜任力提升（二）\n学分: - 学时: - 共2节'],
        # 'mute_button_selector': "button[aria-label='Mute']",
    }
    username = ""
    password = ""
    is_headless = False
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=is_headless, slow_mo=50)
        # browser = p.chromium.connect_over_cdp('http://127.0.0.1:12345')   #指定本地浏览器启动
        page = browser.new_page()
        
        login(page, config, username, password)
        navigate_to_courses(page, config)
        study_courses(page, config, is_headless)
        
        browser.close()

if __name__ == "__main__":
    main()
