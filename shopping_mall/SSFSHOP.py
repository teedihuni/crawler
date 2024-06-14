import csv
import logging
import os
import sys
import time
from collections import defaultdict
from tqdm import tqdm
from selenium.common.exceptions import InvalidSessionIdException
from urllib.parse import quote
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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
    filename='/home/dhlee2/workspace/crawling_code/shopping_mall_crawler/save/log/SSFSHOP.log',
    format="%(asctime)s:%(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, mall, save_path, driver_path):

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

    #세션 에러 시 세션 재시작
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
                logging.warning('Invalid session id , starting a new browser session...')
                self.browser.quit()  # 현재 브라우저 인스턴스 종료
                self.start_browser()  # 새로운 브라우저 인스턴스 시작
                
            except Exception as e:
                print(f'Page Load failed: {page_url} / Error: {e}')
                logging.warning(f'Page Load failed: {page_url} / Error: {e}')
                break
        
    def make_save_folder(self, ctgr, sub_ctgr_1, sub_ctgr_2, brand_name, sex, item_name):
    
        img_folder_path = os.path.join(self.save_path, self.mall ,ctgr, sub_ctgr_1, sub_ctgr_2, brand_name, sex, item_name)        
        os.makedirs(img_folder_path, exist_ok=True)        
        self.ctgr_items_count[sub_ctgr_1] += 1
        
        return img_folder_path

    def download_sumnail_image(self, ctgr, sub_ctgr_1, img_folder_path, item_name, img_info, index, downloaded_imglist):
        
        if 'https' not in img_info:
            img_info = 'https'+img_info

        file_name, file_ext = os.path.splitext(img_info)
        file_name = file_name.split('/')[-1].split('=')[-1]
        file_ext = file_ext if file_ext else '.jpg'
        img_save_path = os.path.join(img_folder_path, file_name+file_ext)

        if file_name not in downloaded_imglist: # 파일명이 리스트에 존재하지 않으면 다운로드 진행
            try:
                
                try: 
                    urlretrieve(img_info, img_save_path)
                except Exception as e:

                    # certifi 권한 문제 해결
                    ssl._create_default_https_context = ssl._create_unverified_context 

                    # 공백, 한글이 주소에 포함되는 경우 전처리
                    encoded_url = quote(img_info, safe='/:[]%')
                    urlretrieve(encoded_url, img_save_path)
                    
                self.ctgr_imgs_count[sub_ctgr_1] +=1
                
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
 
        main_item_image = index == 0

        if index == 0:
            main_item_image = True
        else:
            main_item_image = False

        with open(f'{self.tsv_file_name}.tsv', 'at') as tsv_file: # .tsv 파일 생성
            writer = csv.writer(tsv_file, delimiter='\t')
            writer.writerow([self.mall, item_name, ctgr,img_save_path[self.path_index:], main_item_image])
        
    def get_sumnail_image(self, sex, ctgr, current_url, page_num, idx):
        
        time.sleep(2)
        
        issue_detect = True

        while True:
            try :
                # 브랜드 명 추출
                brand_name_element = self.browser.find_element(By.CSS_SELECTOR, 'h2.brand-name')
                brand_name = change_word(brand_name_element.text)
                
                # 상품
                product_name_element = self.browser.find_element(By.CSS_SELECTOR, 'div.gods-name')
                product_name = change_word(product_name_element.text)

                # 카테고리 정보 추출
                ctgr_tree_element = self.browser.find_elements(By.CSS_SELECTOR, 'div.breadcrumb li')[-1]
                ctgr_tree = ctgr_tree_element.text
                ctgr_tree = ctgr_tree.split('/')
                if len(ctgr_tree) < 2:
                    ctgr_tree.append(ctgr_tree[0])
                sub_ctgr_1 = ctgr_tree[0]
                sub_ctgr_2 = ctgr_tree[1]


                break #정상적으로 추출했으면 탈출

            except InvalidSessionIdException as e:
                self.browser_control(current_url, 'h2.brand-name')
                logging.warning("InvalidSession Error in brand, product extraction")
            
            except Exception as e:
                print("크롬 에러로 해당 상품 패스: {e}")
                logging.warning("chrome error | passing product")
                issue_detect = False
                break
        
        if not issue_detect : # 해결 불가 이슈 처리
            return #함수 종료
        
        print(f'{ctgr} | {page_num} 페이지 {idx+1} 번째 상품 | {brand_name} 브랜드의 {product_name} 상품 처리 중')
        logging.info(f'{ctgr} | {page_num} 페이지 {idx+1} 번째 상품 | {brand_name} 브랜드의 {product_name} 상품 처리 중')
        
         # 이미지 추출            
        try: 
            img_container= self.browser.find_element(By.CSS_SELECTOR,'#godsTabView > div.gods-detail-img')
            img_elements = BeautifulSoup(img_container.get_attribute('innerHTML'), features='html.parser').select('img')
            attributes = ['data-original','src'] # 상세페이지마다 이미지 속성이 다른 경우 커버
            img_url_list = [elements.get(attrs) for elements in img_elements for attrs in attributes if elements.get(attrs)]
        
        except Exception as e:
            print(f'이미지 추출 에러 : {e}')


        # 상품 이미지 저장
        try: 
            if img_url_list :
                img_folder_path = self.make_save_folder(ctgr, sub_ctgr_1, sub_ctgr_2, brand_name, sex, product_name)
                downloaded_imglist = [os.path.splitext(path)[0] for path in os.listdir(img_folder_path)] 
                for index, img_info in enumerate(img_url_list):
                    self.download_sumnail_image(ctgr, sub_ctgr_1, img_folder_path, product_name, img_info, index, downloaded_imglist)

            else:
                print('상품이미지가 없음')
        except Exception as e:
            print(f'상품 이미지 저장 에러 : {e}')
            logging.info(f'상품 이미지 저장 에러 : {e}')
            return
                           
        

    def do_crawling(self, ctgr_link_tree):
        # 29CM 카테고리별 크롤링
        for sex, main_ctgr , ctgr_link, unique_link in (ctgr_link_tree):
            self.tsv_file_name = os.path.join(self.save_path, f'{self.mall}/{change_tsv_name(main_ctgr)}_{get_current_time()}') # .tsv 파일명 지정
            with open(f'{self.tsv_file_name}.tsv', 'wt') as tsv_file: # .tsv 파일 생성
                writer = csv.writer(tsv_file, delimiter='\t')
                writer.writerow(['mall_name', 'product_name', 'category', 'path', 'main'])
            
            page_num = 1
            
            while True:
                # 현재 URL 저징                
                page_url = f'https://www.ssfshop.com/{ctgr_link}/list?dspCtgryNo={unique_link}&currentPage={page_num}&sortColumn=SALE_QTY_SEQ&serviceType=DSP&ctgrySectCd=GNRL_CTGRY&fitPsbYn=N'

                # 카테고리별 페이지 로드
                print(f'Crawling category {main_ctgr} - Start page {page_num} ....')
                logging.info(f'Crawling category {main_ctgr} - Start page {page_num} ....')
                
                self.browser_control(page_url,'div.list_goods')                    
                time.sleep(2)
                
                # 페이지 내 상품 개수 추출
                try:
                    item_count_inpage = len(self.browser.find_elements(By.CSS_SELECTOR,'#dspGood > li > a'))             
                    
                # 다음 페이지가 존재하지 않는 경우 카테고리 크롤링 종료
                except Exception as e:
                    print(f'Page error: {e} / URL: {page_url}')
                    logging.warning(f'Page error: {e} / URL: {page_url}')
                    break
                
                # 상품 리스트가 존재하지 않는 경우 카테고리 크롤링 종료
                if item_count_inpage == 0 :
                    print(f'Item not found - URL: {page_url}')
                    logging.warning(f'Item not found - URL: {page_url}')
                    break

                # test 세팅
                if page_num == 2:
                    break
                
                # 상품 진입 링크가 없어서 click 방식으로 진입                           
                for idx in tqdm(range(item_count_inpage),desc='진행중'):
                    
                    # test 세팅
                    if idx == 2:
                        break
                        
                    if idx > 0:
                        self.browser.get(page_url)
                        # 페이지 정보가 로드될 때 까지 대기
                        self.wait_page.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.list_goods')))
                    
                    time.sleep(2)
                    item_elements = self.browser.find_elements(By.CSS_SELECTOR,'#dspGood > li > a')
                    button = item_elements[idx]
                    button.click()

                    current_url = self.browser.current_url
                    # 학습 이미지 크롤링             
                    self.get_sumnail_image(sex, main_ctgr, current_url ,page_num, idx)

                page_num += 1

            category_exit_msg_v2(main_ctgr, page_num-1, self.ctgr_items_count, self.ctgr_imgs_count)
            #
        
        # 크롤링 요약 정보 저장
        ctgr_info_file_name = os.path.join(self.save_path, f'{self.mall}/크롤링요약_{get_current_time()}.tsv')
        file_exists = os.path.isfile(ctgr_info_file_name)
        with open(f'{ctgr_info_file_name}', 'a', newline = '') as ctgr_info_file:
            writer = csv.writer(ctgr_info_file, delimiter='\t')

            if not file_exists:
                writer.writerow(['category', 'product_count','image_count'])
            for (ctgr_info, product_count),(_, image_count) in zip(sorted(self.ctgr_items_count.items()),sorted(self.ctgr_imgs_count.items())):
                writer.writerow([main_ctgr, ctgr_info, product_count, image_count, get_current_timenow()])
                
import os, os.path as osp
SAVE_PATH = '/home/dhlee2/workspace/crawling_code/shopping_mall_crawler/save'							
DRIBER_PATH = osp.join(os.getcwd(), 'selenium_driver', 'chromedriver')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delete same image of crawling images.')
    parser.add_argument('--mall', type=str, default='SSFSHOP', metavar='SHOPPING_MALL',
                        help='Target shopping mall name')
    parser.add_argument('--save-path', type=str, default=SAVE_PATH, metavar='DIR_PATH',
                        help='Directory path to save crawling images')
    parser.add_argument('--driver-path', type=str, default=DRIBER_PATH, metavar='DIR_PATH',
                        help='Directory path to saved chrome driver files')
    args = parser.parse_args()

    if not os.path.isdir(f'{args.save_path}/{args.mall}'):
        os.mkdir(f'{args.save_path}/{args.mall}')

    # 카테고리 크롤링    
    category_link_tree = [['여성','신발','WomensShoes','SFMA46A12'], 
                          ['남성','신발','MensShoes','SFMA46A18']]

    # category_link_tree = [['아우터','Outerwear','SFMA41A07'],['아우터','Outerwear','SFMA42A05'],
    #                 ['하의','Pants-Trousers','SFMA41A04'], ['하의','Pants-Trousers','SFMA42A04'],
    #                 ['치마','Skirts','SFMA41A05']]

    crawler = Crawler(args.mall, args.save_path, args.driver_path)
    crawler.do_crawling(category_link_tree)
    
    print('\n===== Crawling Summary =====')
    logging.info('===== Crawling Summary =====')

    print('-----All Items -----')
    logging.info('----- All Items -----')
    for key, val in crawler.ctgr_items_count.items():
        print(f'  {key} category: {val} items.')
        logging.info(f'  {key} category: {val} items.')

    print('----- All Images -----')
    logging.info('----- All Images -----')
    for key, val in crawler.ctgr_imgs_count.items():
        print(f'  {key} category: {val} images.')
        logging.info(f'  {key} category: {val} images.')


