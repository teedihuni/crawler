import csv
import logging
import os
import sys
import time
from collections import defaultdict
from tqdm import tqdm
from selenium.common.exceptions import InvalidSessionIdException


import argparse
import magic
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PROJECT_FOLDER_PATH = './'
sys.path.append(PROJECT_FOLDER_PATH)
from utils import *
from selenium_driver.selenium_init import *

logging.basicConfig(
    level=logging.INFO, # level=logging.DEBUG,
    filename='./save/log/29cm_new2.log',
    format="%(asctime)s:%(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, mall, save_path, driver_path):
        self.category_url = 'https://shop.29cm.co.kr/category/list?colors=&categoryLargeCode=268100100&categoryMediumCode=' # 여성 의류 카테고리 진입 페이지
        self.sex = '여성' 
        # self.category_url = 'https://shop.29cm.co.kr/category/list?colors=&categoryLargeCode=272100100&categoryMediumCode=' # 남성 카테고리 진입 페이지
        self.tsv_file_name = '' # .tsv 파일명
        self.mall = mall # 크롤링 대상 쇼핑몰
        self.save_path = save_path # 저장 경로 저장
        self.driver_path = driver_path
        self.path_index = len(save_path) - len(save_path.rstrip('/').split('/')[-1]) # 저장 경로 제거를 위한 index 계산
        self.ctgr_items_count = defaultdict(int) # 세부 카테고리별 크롤링 상품 개수
        self.ctgr_imgs_count = defaultdict(int)


        # OS에 따른 chromedriver 선택
        executable = detect_system_os(driver_path)

        # Chrome webdriver 설정
        self.browser = browser_options(executable)
        self.wait_page = WebDriverWait(self.browser, 100)

    def start_browser(self):
        #세션 에러를 위한 브라우저 인스턴스를 시작
        executable = detect_system_os(self.driver_path)
        self.browser = browser_options(executable)
        self.wait_page = WebDriverWait(self.browser, 100)
        
    def browser_control(self, page_url, condition):
        while True:
            try:
                # 상품 리스트 페이지 요청
                time.sleep(get_random_number())
                self.browser.get(page_url)
                # 페이지 정보가 로드될 때 까지 대기
                self.wait_page.until(EC.presence_of_element_located((By.CSS_SELECTOR, condition)))
                break
                
            except InvalidSessionIdException:
                # Invalid Session Id Exception에 대한 특별한 처리
                print('Invalid session id , starting a new browser session...')
                self.browser.quit()  # 현재 브라우저 인스턴스 종료
                self.start_browser()  # 새로운 브라우저 인스턴스 시작
                
            except Exception as e:
                print(f'Page Load failed: {page_url} / Error: {e}')
                logging.warning(f'Page Load failed: {page_url} / Error: {e}')
                break
    
    def make_save_folder(self, main_ctgr, sub_ctgr, brand_name , sex, item_name):
        
        img_folder_path = os.path.join(self.save_path, self.mall ,main_ctgr, sub_ctgr, change_word(brand_name) , sex, change_word(item_name))
        os.makedirs(img_folder_path, exist_ok=True)
        self.ctgr_items_count[sub_ctgr] += 1
        
        return img_folder_path

    def download_sumnail_image(self, sub_ctgr ,img_folder_path, item_name, img_info, downloaded_imglist):
        
        if not img_info.startswith('https'): 
            img_link = 'https:'+img_info
        else:
            img_link = img_info 

        file_name, file_ext = os.path.splitext(img_link)
        file_name = file_name.split('/')[-1].split('=')[-1]
        file_ext = file_ext if file_ext else '.jpg'
        img_save_path = os.path.join(img_folder_path, file_name+file_ext)

        if file_name not in downloaded_imglist: # 파일명이 리스트에 존재하지 않으면 다운로드 진행
            try:
                # 파일이 존재하지 않으면 다운로드 시도
                urlretrieve(img_info, img_save_path)
                self.ctgr_imgs_count[sub_ctgr] +=1
                
                # MIME 타입 확인 및 파일 확장자 변경
                mime_type = magic.from_file(img_save_path, mime=True).split('/')[-1]
                if file_ext != mime_type:  # 확장자 앞의 점(.) 제거
                    new_file_path = os.path.splitext(img_save_path)[0] + '.' + mime_type
                    os.rename(img_save_path, new_file_path)
                    img_save_path = new_file_path
            except Exception as e:
                print(f'Save failed: {img_info} / Error: {e}')
                logging.warning(f'Save failed: {img_info} / Error: {e}')
                return
        #else:
            #print(f'File already exists: {img_save_path}')
            #logging.warning(f'img {file_name} already exists : {img_save_path}')
            
        
    def get_sumnail_image(self, item_link, main_ctgr, sub_ctgr):
        if 'http' in item_link:
            url_link = item_link

        # 29CM 상품 페이지 요청
        self.browser_control(url_link, 'div.css-dluqe2.ei3q66x2')            

        # 29CM 썸네일 정보 추출
        time.sleep(2)
        try: 
            img_container = self.browser.find_elements(By.XPATH, '//div[contains(@class, "react-transform-wrapper") and contains(@class, "transform-component-module_wrapper__1_Fgj")]//img')
            final_img_links = [img.get_attribute('src') for img in img_container]

        except Exception as e:
            print(f'썸네일 정보 추출 에러 : {e}')
            final_img_links = []

        # 상품명 & 브랜드 명 추출
        try :
            item_name_element = self.browser.find_element(By.ID,'pdp_product_name')
            item_name = item_name_element.text
            
            brand_name_element = self.browser.find_element(By.CLASS_NAME, 'css-1dncbyk')
            brand_name = brand_name_element.text
            
        except Exception as e:
            print(f'상품명 & 브랜드 명 추출 에러 : {e}')
        

        # 상품 이미지 저장
        try: 
            if len(final_img_links) >= 1:
                img_folder_path = self.make_save_folder(main_ctgr, sub_ctgr, brand_name , self.sex,item_name)
                downloaded_imglist = [os.path.splitext(path)[0] for path in os.listdir(img_folder_path)] 
                for index, img_info in enumerate(final_img_links):
                    self.download_sumnail_image(sub_ctgr ,img_folder_path, item_name, img_info, downloaded_imglist)
            else:
                print('상품이미지가 없음')
        except Exception as e:
            print(f'상품 이미지 저장 에러 : {e}')
            logging.info(f'상품 이미지 저장 에러 : {e}')
        

    def do_crawling(self, ctgr_id_info):
        # 29CM 카테고리별 크롤링
        for main_ctgr, value in ctgr_id_info.items(): #main_ctgr = '바지'
                
            for main_num, sub_value in value.items(): #main_num : 바지 url num

                #print(main_ctgr, main_num)
                for sub_ctgr, sub_num in sub_value.items(): #sub_ctgr = '쇼츠' sub_num : 쇼츠에 대한 url num
                    #print(sub_ctgr, sub_num)
                    
                    # self.tsv_file_name = os.path.join(self.save_path, f'{self.mall}/{change_tsv_name(sub_ctgr)}_{get_current_time()}') # .tsv 파일명 지정
                    # with open(f'{self.tsv_file_name}.tsv', 'wt') as tsv_file: # .tsv 파일 생성
                    #     writer = csv.writer(tsv_file, delimiter='\t')
                    #     writer.writerow(['mall_name', 'product_name', 'category', 'path', 'main'])

                    page_num = 1 # 페이지 번호
                    page_url = '' # 상품 리스트 페이지 URL

                    sub_link = f'{main_num}&categorySmallCode={sub_num}&minPrice=&maxPrice=&isFreeShipping=&excludeSoldOut=&isDiscount=&brands=&sort=RECOMMEND&defaultSort=RECOMMEND&sortOrder=DESC&tag=&page={page_num}'
                    main_link = self.category_url+sub_link 


                    while True:

                        sub_link = f'{main_num}&categorySmallCode={sub_num}&minPrice=&maxPrice=&isFreeShipping=&excludeSoldOut=&isDiscount=&brands=&sort=RECOMMEND&defaultSort=RECOMMEND&sortOrder=DESC&tag=&page={page_num}'
                        main_link = self.category_url+sub_link 

                        # 카테고리별 페이지 로드
                        self.browser_control(main_link, 'div.css-8atqhb')
                        print(f'Crawling category {main_ctgr} | {sub_ctgr} - Start page {page_num} ....')
                        logging.info(f'Crawling category {main_ctgr} | {sub_ctgr}  - Start page {page_num} ....')
                        time.sleep(2)
                        # 29CM 상품 리스트 추출
                        try:
                            item_element = self.browser.find_elements(By.CSS_SELECTOR,'li.css-1teigi4.e1114pfz0 > a')
                            item_links = [element.get_attribute('href') for element in item_element]
                            
                        # 다음 페이지가 존재하지 않는 경우 카테고리 크롤링 종료
                        except Exception as e:
                            print(f'Page not found: {e} / URL: {page_url}')
                            logging.error(f'Page not found: {e} / URL: {page_url}')
                            break
                        
                        # 상품 리스트가 존재하지 않는 경우 카테고리 크롤링 종료
                        if not item_links:
                            print(f'Item not found - URL: {page_url}')
                            logging.error(f'Item not found - URL: {page_url}')
                            break
                            
                        # test 세팅
                        item_links = item_links[:2]
                        if page_num == 3:
                            break

                        # 학습 이미지 크롤링                
                        for item_link in tqdm(item_links, desc='진행중'):
                            tqdm.write(f'{main_ctgr} - {sub_ctgr}의 {page_num} page | {item_link} 크롤링 중')
                            logging.info(f'{main_ctgr} - {sub_ctgr}의 {page_num} page | {item_link} 크롤링')
                            self.get_sumnail_image(item_link, main_ctgr, sub_ctgr)

                        page_num += 1

                    category_exit_msg_v2(sub_ctgr, page_num , self.ctgr_items_count, self.ctgr_imgs_count)
                    #os.rename(f'{self.tsv_file_name}.tsv', f'{self.tsv_file_name}_{get_current_time()}.tsv') # .tsv 파일명 변경
                
                # 카테고리 정보 저장
                ctgr_info_file_name = os.path.join(self.save_path, f'{self.mall}/카테고리_{get_current_time()}.tsv')
                with open(f'{ctgr_info_file_name}.tsv', 'wt') as ctgr_info_file:
                    writer = csv.writer(ctgr_info_file, delimiter='\t')
                    writer.writerow(['category', 'product_count','image_count'])
                    for (ctgr_info, product_count),(_, image_count) in zip(sorted(self.ctgr_items_count.items()),sorted(self.ctgr_imgs_count.items())):

                        writer.writerow([main_ctgr, ctgr_info, product_count, image_count])
                
import os, os.path as osp
SAVE_PATH = osp.join(os.getcwd(), 'save')						
DRIBER_PATH = osp.join(os.getcwd(), 'selenium_driver', 'chromedriver')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delete same image of crawling images.')
    parser.add_argument('--mall', type=str, default='29cm', metavar='SHOPPING_MALL',
                        help='Target shopping mall name')
    parser.add_argument('--save-path', type=str, default=SAVE_PATH, metavar='DIR_PATH',
                        help='Directory path to save crawling images')
    parser.add_argument('--driver-path', type=str, default=DRIBER_PATH, metavar='DIR_PATH',
                        help='Directory path to saved chrome driver files')
    args = parser.parse_args()

    if not os.path.isdir(f'{args.save_path}/{args.mall}'):
        os.mkdir(f'{args.save_path}/{args.mall}')

    # 여성 
    ctgr_tree = {'하의':{'268106100': {'쇼트':'268106108','레깅스':'268106109'}},
                 '치마' : {'268107100':{'미니':'268107101'}},
                 '속옷' : {'268109100':{'브라':'268109101','팬티':'268109102','세트':'268109103'}},
                 '수영복' : {'268108100' :{'원피스_모노키니' : '268108103' ,'비키니' : '268108104' ,'래쉬가드' : '268108105','커버업' : '268108106'}}
                 
                 }
    # 남성
    ctgr_tree = {'하의' :{'272104100':{'레깅스':'272104110','쇼트':'272104108'}},
                 '속옷' : {'272105100':{'팬티':'272105101','언더셔츠':'272105102'}}
                 }


    crawler = Crawler(args.mall, args.save_path, args.driver_path)
    crawler.do_crawling(ctgr_tree)
    
    print('\n===== Crawling Summary =====')
    logging.info('===== Crawling Summary =====')

    print('----- Products -----')
    logging.info('----- Products -----')
    for key, val in crawler.ctgr_items_count.items():
        print(f'  {key} category: {val} items.')
        logging.info(f'  {key} category: {val} items.')

    print('----- Images-----')
    logging.info('----- Images -----')
    for key, val in crawler.ctgr_imgs_count.items():
        print(f'  {key} category: {val} items.')
        logging.info(f'  {key} category: {val} items.')

