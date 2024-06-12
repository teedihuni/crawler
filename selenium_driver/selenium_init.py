from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService

import os
import platform

from selenium import webdriver
import random

__all__ = ['detect_system_os', 'browser_options', 'check_broswer_version']

user_agent = ["user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
              "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.20 Safari/537.36",
              "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.87 Safari/537.36",
              "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
              "user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2919.83 Safari/537.36",
              "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2656.18 Safari/537.36",
              "user-agent=Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
              "user-agent=Mozilla/5.0 (X11; OpenBSD i386) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
              "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36"]


def detect_system_os(driver_path):
    # OS에 따른 chromedriver 선택
    if platform.system() == 'Windows':
        print('Detected OS : Windows')
        return os.path.join(driver_path, 'chromedriver_win.exe')
    elif platform.system() == 'Linux':
        print('Detected OS : Linux')
        
        new_path =os.path.join(driver_path, 'chromedriver_linux')
        
        return os.path.join(driver_path, 'chromedriver_linux')
        
    elif platform.system() == 'Darwin':
        print('Detected OS : Mac')
        return os.path.join(driver_path, 'chromedriver_mac')
    else:
        raise OSError('Unknown OS Type')


def browser_options(excutable):
    # Chrome webdriver 설정
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized") # Chrome window 최대화
    # chrome_options.add_argument('--headless') # GUI 사용 안함
    chrome_options.add_argument('--no-sandbox') # Chrome sandbox 사용 안함
    chrome_options.add_argument("--enable-automation") # 접근성 트리 사용
    chrome_options.add_argument('--disable-dev-shm-usage') # Linux /dev/shm 공유 메모리 사용 안함
    chrome_options.add_argument("--disable-gpu") # GPU 사용 안함
    chrome_options.add_argument("--disable-infobars") # 상단에 표기되는 정보표시줄 사용 안함
    chrome_options.add_argument("--disable-browser-side-navigation") # Navigation 기능 사용 안함
    # chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # 이미지 로딩 비활성화
    # chrome_options.add_argument(random.choice(user_agent))

    # get default service instance
    service = ChromeService(excutable_path=excutable)

    return webdriver.Chrome(service=service, options=chrome_options)


def check_broswer_version(browser):
    # Chrome browser, Chrome webdriver 버전 비교
    browser_version = 'Failed to detect version'
    chromedriver_version = 'Failed to detect version'
    major_version_different = False

    if 'browserVersion' in browser.capabilities:
        browser_version = str(browser.capabilities['browserVersion'])

    if 'chrome' in browser.capabilities:
        if 'chromedriverVersion' in browser.capabilities['chrome']:
            chromedriver_version = str(browser.capabilities['chrome']['chromedriverVersion']).split(' ')[0]

    if browser_version.split('.')[0] != chromedriver_version.split('.')[0]:
        major_version_different = True

    print('_________________________________')
    print('Current web-browser version:\t{}'.format(browser_version))
    print('Current chrome-driver version:\t{}'.format(chromedriver_version))
    if major_version_different:
        print('warning: Version different')
        print('Download correct version at "http://chromedriver.chromium.org/downloads" and place in "./chromedriver"')
    print('_________________________________')
    