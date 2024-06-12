import csv
import logging
import os
import random
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
from soupsieve.css_parser import FLG_PLACEHOLDER_SHOWN

PROJECT_FOLDER_PATH = './'
sys.path.append(PROJECT_FOLDER_PATH)
from utils import *
from selenium_driver.selenium_init import *

logging.basicConfig(
    level=logging.INFO, # level=logging.DEBUG,
    filename='/home/crawling/crawling/crawling_img_save/crawling/log/Musinsa.log',
    format="%(asctime)s:%(levelname)s:%(message)s"   
)
logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, mall, save_path, driver_path):
        self.category_url = 'https://search.musinsa.com/category/' # 카테고리 진입 페이지
        self.crawling_ctgr = '카테고리' # 크롤링 대상 카테고리
        self.tsv_file_name = '' # .tsv 파일명
        self.mall = mall # 크롤링 대상 쇼핑몰
        self.save_path = save_path # 저장 경로 저장
        self.driver_path = driver_path
        self.path_index = len(save_path) - len(save_path.rstrip('/').split('/')[-1]) # 저장 경로 제거를 위한 index 계산
        self.plural_ctgr_count = defaultdict(int) # 복수 이미지의 카테고리별 크롤링 상품 개수
        self.single_ctgr_count = defaultdict(int) # 단수 이미지의 카테고리별 크롤링 상품 개수
        self.ctgr_items_count = defaultdict(int) # 세부 카테고리별 크롤링 상품 개수

        # OS에 따른 chromedriver 선택
        executable = detect_system_os(driver_path)

        # Chrome webdriver 설정
        self.browser = browser_options(executable)
        self.wait_page = WebDriverWait(self.browser, 10)
        
    def start_browser(self):
        #세션 에러를 위한 브라우저 인스턴스를 시작
        executable = detect_system_os(self.driver_path)
        self.browser = browser_options(executable)
        self.wait_page = WebDriverWait(self.browser, 100)
    
    def make_save_folder(self, ctgr, brand_name, item_name, number):
        img_folder_path = os.path.join(self.save_path, self.mall, brand_name, ctgr, number, change_word(item_name))
        
        os.makedirs(img_folder_path, exist_ok=True)
        # 카테고리별 크롤링 상품 개수 수정
        if number == 'Plural':
            self.plural_ctgr_count[ctgr] += 1
        else:
            self.single_ctgr_count[ctgr] += 1
        
        return img_folder_path

    def download_sumnail_image(self, img_folder_path, item_name, img_info, index, downloaded_imglist):     
        
        img_link = img_info            

        file_name, file_ext = os.path.splitext(img_link)
        file_name = file_name.split('/')[-1].split('=')[-1]
        file_ext = file_ext if file_ext else '.jpg'
        img_save_path = os.path.join(img_folder_path, file_name+file_ext)

        if file_name not in downloaded_imglist: # 파일명이 리스트에 존재하지 않으면 다운로드 진행
            try:
                # 파일이 존재하지 않으면 다운로드 시도
                urlretrieve(img_info, img_save_path)
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
        else:
            #print(f'File already exists: {img_save_path}')
            logging.warning(f'img {file_name} already exists : {img_save_path}')
        main_item_image = index == 0

        with open(f'{self.tsv_file_name}.tsv', 'at') as tsv_file: # .tsv 파일 생성
            writer = csv.writer(tsv_file, delimiter='\t')
            writer.writerow([self.mall, item_name, img_save_path[self.path_index:], main_item_image])
        
    def get_sumnail_image(self, item_link, brand_name, item_name, ctgr):
        if 'http' in item_link:
            url_link = item_link

        try:
            # 무신사 상품 페이지 요청
            time.sleep(get_random_number())
            self.browser.get(url_link)
            # 상품 정보가 로드될 때 까지 대기
            self.wait_page.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#page_product_detail > div.right_area.page_detail_product')))
        
        except InvalidSessionIdException:
            # Invalid Session Id Exception에 대한 특별한 처리
            print('Invalid session id , starting a new browser session...')
            logging.warning(f'browser session out')
            self.browser.quit()  # 현재 브라우저 인스턴스 종료
            self.start_browser()  # 새로운 브라우저 인스턴스 시작
            return
        
        except Exception as e:
            print(f'Item Load failed: {url_link} / Error: {e}')
            logging.warning(f'Item Load failed: {url_link} / Error: {e}')
            return
        
        time.sleep(2)
        # 상품 상세 이미지 추출
        time.sleep(3)
        try: 
            img_list_element = self.browser.find_elements(By.CSS_SELECTOR,'section.product-detail__sc-5zi22l-0.tACkg img')
            img_links = [link.get_attribute('src') for link in img_list_element]        
        except Exception as e:
            print(e)

        if not img_links:
            return

        # 비디오 썸네일 제거
        try :
            video_sumnail = []
            for index, img_info in enumerate(img_list_element):
                if img_info.get_attribute('class') == 'video_thumb':
                    video_sumnail.append(index)
            
            for index in video_sumnail:
                del img_list_element[index]
        except Exception as e:
            print(e)
            
            # 상품 이미지 저장
        try: 
            if len(img_links) > 1:
                img_folder_path = self.make_save_folder(ctgr, brand_name ,item_name, 'Plural')
                downloaded_imglist = [os.path.splitext(path)[0] for path in os.listdir(img_folder_path)] 
                for index, img_info in enumerate(img_links):
                    self.download_sumnail_image(img_folder_path, item_name, img_info, index,downloaded_imglist)
            else:
                img_folder_path = self.make_save_folder(ctgr, brand_name ,item_name, 'Single')
                downloaded_imglist = [os.path.splitext(path)[0] for path in os.listdir(img_folder_path)]
                self.download_sumnail_image(img_folder_path,  item_name, img_links[0], 0, downloaded_imglist)
        except Exception as e:
            print(e)
        
        
            

    def do_crawling(self, ctgr_link, ctgr_name, brand_lists):
        # 무신사 카테고리별 크롤링
        
        for brand_name in brand_lists:
            for ctgr, link,  in zip(ctgr_name, ctgr_link):
                self.tsv_file_name = os.path.join(f'{self.save_path}{self.mall}', f'{brand_name}_{change_tsv_name(self.crawling_ctgr)}>{change_tsv_name(ctgr)}_{get_current_time()}') # .tsv 파일명 지정
                with open(f'{self.tsv_file_name}.tsv', 'wt') as tsv_file: # .tsv 파일 생성
                    writer = csv.writer(tsv_file, delimiter='\t')
                    writer.writerow(['mall_name', 'product_name', 'category', 'path', 'main'])

                
                page_url = '' # 상품 리스트 페이지 URL
                page_num = 1          

                # 페이지 로드

                while True:
                    print(f'Crawling {brand_name} {ctgr} - Start page {page_num} ....')
                    logging.info(f'Crawling {brand_name} {ctgr} - Start page {page_num} ....')
                    main_link = f'https://www.musinsa.com/categories/item/{link}?d_cat_cd={link}&brand={brand_name}&=small&sort=pop_category&sub_sort=&page={page_num}&display_cnt=90&group_sale=&exclusive_yn=&sale_goods=&timesale_yn=&ex_soldout=&plusDeliveryYn=&kids=&color=&price1=&price2=&shoeSizeOption=&tags=&campaign_id=&includeKeywords=&measure='

                    # 현재 URL 저장
                    while True:
                        try:
                            # 상품 리스트 페이지 요청
                            time.sleep(get_random_number())
                            self.browser.get(main_link)
                            # 페이지 정보가 로드될 때 까지 대기
                            self.wait_page.until(EC.presence_of_element_located((By.ID, 'searchList')))
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

                    # 무신사 상품 리스트 추출
                    
                    time.sleep(2)
                    try:
                        item_element = self.browser.find_element(By.CLASS_NAME,'boxed-list-wrapper')
                        item_table = BeautifulSoup(item_element.get_attribute('innerHTML'), features='html.parser')
                        item_list = item_table.select('div > ul > li > div.li_inner > div.list_img > a')
                        
                    # 다음 페이지가 존재하지 않는 경우 카테고리 크롤링 종료
                    except Exception as e:
                        print(f'Page not found: {e} / URL: {page_url}')
                        logging.error(f'Page not found: {e} / URL: {page_url}')
                        break
                    
                    # 상품 리스트가 존재하지 않는 경우 카테고리 크롤링 종료
                    if not item_list:
                        print(f'Item not found - URL: {page_url}')
                        logging.error(f'Item not found - URL: {page_url}')
                        break
                    
                    time.sleep(3)
                    # 브랜드 및 상품명 추출
                    try:
                        item_element = self.browser.find_element(By.CLASS_NAME,'boxed-list-wrapper')
                        item_table = BeautifulSoup(item_element.get_attribute('innerHTML'), features='html.parser')
                        brand_lists = item_table.select('div > ul > li > div.li_inner > div.article_info > p.item_title > a')
                        brand_name_kor = [brand.text for brand in brand_lists][0]
                        product_lists = item_table.select('div > ul > li > div.li_inner > div.article_info > p.list_info > a')
                        product_names = [product.attrs['title'] for product in product_lists]
                        
                        
                    # 다음 페이지가 존재하지 않는 경우 카테고리 크롤링 종료
                    except Exception as e:
                        print(f'Page not found: {e} / URL: {page_url}')
                        logging.error(f'Page not found: {e} / URL: {page_url}')
                        break
                    

                    del product_lists
                    del brand_lists
                    
                    # 무신사 상품별 URL
                    item_links = []
                    for item_table in item_list:
                        item_links.append('https://'+item_table.attrs['href'].lstrip('/app'))

                    # test 세팅
                    # item_links = item_links[40:]
                    # if page_num == 2:
                    #     break
                    
                    # 학습 이미지 크롤링
                    for idx in tqdm(range(len(item_links))):
                        print(f'{brand_name} | {ctgr} | {page_num}page | {idx} 번째 상품 crawling 중 : {item_links[idx]}')                       

                        self.get_sumnail_image(item_links[idx], brand_name_kor, product_names[idx], ctgr)
                        self.get_sumnail_image(item_links[idx], brand_name_kor, product_names[idx], ctgr)
                        
                    page_num += 1

            brand_category_exit_msg(ctgr, brand_name, page_num-1, self.plural_ctgr_count, self.single_ctgr_count)
            new_tsv_name = os.path.join(f'{self.save_path}{self.mall}', f'{brand_name_kor}_{change_tsv_name(self.crawling_ctgr)}>{change_tsv_name(ctgr)}') # .tsv 파일명 지정


            os.rename(f'{self.tsv_file_name}.tsv', f'{new_tsv_name}_{get_current_time()}.tsv') # .tsv 파일명 변경
        
        # 카테고리 정보 저장
        ctgr_info_file_name = os.path.join(self.save_path, f'{self.mall}_카테고리_{get_current_time()}.tsv')
        with open(f'{ctgr_info_file_name}.tsv', 'wt') as ctgr_info_file:
            writer = csv.writer(ctgr_info_file, delimiter='\t')
            writer.writerow(['category', 'count'])
            for ctgr_info, count in sorted(self.ctgr_items_count.items()):
                writer.writerow([ctgr_info, count])

import os, os.path as osp
SAVE_PATH = '/home/crawling/crawling/crawling_img_save/crawling/'										
DRIBER_PATH = osp.join(os.getcwd(), 'selenium_driver', 'chromedriver')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delete same image of crawling images.')
    parser.add_argument('--mall', type=str, default='Musinsa', metavar='SHOPPING_MALL',
                        help='Target shopping mall name')
    parser.add_argument('--save-path', type=str, default=SAVE_PATH, metavar='DIR_PATH',
                        help='Directory path to save crawling images')
    parser.add_argument('--driver-path', type=str, default=DRIBER_PATH, metavar='DIR_PATH',
                        help='Directory path to saved chrome driver files')
    args = parser.parse_args()

    if not os.path.isdir(f'{args.save_path}{args.mall}'):
        os.mkdir(f'{args.save_path}{args.mall}')

    # 카테고리 크롤링
    
    category_link = ['003']
    category_name = ['바지']
    category_link = ['003']
    category_name = ['바지']

    # 브랜드 리스트 파일 경로 설정
    file_path = '/home/crawling/crawling/shopping_mall_crawler/shopping_mall/brand_list(아우터).txt'

    # 불러온 리스트를 저장할 변수 초기화
    brand_lists = []

    # 파일이 존재하는지 확인하고, 존재한다면 파일의 내용을 리스트로 변환합니다.
    try:
        # 파일을 엽니다.
        with open(file_path, 'r', encoding='utf-8') as file:
            # 파일의 각 줄을 읽어와 공백을 제거하고 리스트에 추가합니다.
            brand_lists = [line.strip() for line in file]
    except FileNotFoundError:
        print(f"The file at {file_path} was not found.")
    
    crawler = Crawler(args.mall, args.save_path, args.driver_path)
    crawler.do_crawling(category_link, category_name, brand_lists)
    
    print('\n===== Crawling Summary =====')
    logging.info('===== Crawling Summary =====')

    print('----- Plural Items -----')
    logging.info('----- Plural Items -----')
    for key, val in crawler.plural_ctgr_count.items():
        print(f'  {key} category: {val} items.')
        logging.info(f'  {key} category: {val} items.')

    print('----- Single Items -----')
    logging.info('----- Single Items -----')
    for key, val in crawler.single_ctgr_count.items():
        print(f'  {key} category: {val} items.')
        logging.info(f'  {key} category: {val} items.')


