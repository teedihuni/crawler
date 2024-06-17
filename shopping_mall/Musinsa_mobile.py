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
    filename='./save/log/Musinsa_new.log',
    format="%(asctime)s:%(levelname)s:%(message)s"    
)
logger = logging.getLogger(__name__)


'''
2024.06.04 일자로 무신사 pc페이지는 모두 모바일 버전으로 변경되었음
* 모바일 버전은 pc ui와 다르게 카테고리별로 상품이 없고 스크롤을 내려야함 
* 대신 스크롤 내리다보면 이전 상품들에 대한 html 정보가 유지되지 않고 사라지기에 처음 로딩 기준 최대로 스크롤 해서 html 값 받아왔옴
    * orderdict 활용해서 항상 같은 순서를 유지하도록 item_list를 구성
* 상품 내부 페이지도 스크롤을 끝까지 내려야 정상적으로 이미지 주소값이 받아짐(안그러면 일부만 받아짐)
* 카테고리별로 수집하는 이미지와 상품 수 정보를 저장하는 .tsv 파일에 시간 정보 추가 및 새로 돌려도 파일을 다시 만드는 것이 아닌 기존 삽입 정보 밑에 추가
'''

class Crawler:
    def __init__(self, mall, save_path, driver_path, test):
        self.tsv_file_name = '' # .tsv 파일명
        self.mall = mall # 크롤링 대상 쇼핑몰
        self.save_path = save_path # 저장 경로 저장
        self.driver_path = driver_path
        self.testing = test
        self.path_index = len(save_path) - len(save_path.rstrip('/').split('/')[-1]) # 저장 경로 제거를 위한 index 계산
        self.ctgr_items_count = defaultdict(int) # 세부 카테고리별 크롤링 상품 개수
        self.ctgr_imgs_count = defaultdict(int) # 세부 카테고리별 크롤링 이미지 개수

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

    def page_scrolldown2bottom(self):
        ## 상품 정보 전체 띄우기(하단까지 계속 스크롤)
        last_height = self.browser.execute_script("return document.body.scrollHeight")

        while True:
            # 페이지의 하단으로 스크롤
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # 페이지 로드를 기다림
            time.sleep(2)  # 적절한 로딩 시간 부여
            # 새로운 높이 계산
            new_height = self.browser.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break  # 더 이상 스크롤할 페이지가 없을 때
            last_height = new_height  # 새로운 높이를 이전 높이로 업데이트

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
    
    def make_save_folder(self, main_ctgr, sub_ctgr, brand_name , sex_info, item_name):
        
        img_folder_path = os.path.join(self.save_path, self.mall, main_ctgr, sub_ctgr, brand_name , sex_info, item_name)    
        os.makedirs(img_folder_path, exist_ok=True)        
        self.ctgr_items_count[sub_ctgr] += 1
        
        return img_folder_path

    def download_sumnail_image(self, img_folder_path, item_name, img_info, index, ctgr):     
        
        img_link = img_info            

        file_name, file_ext = os.path.splitext(img_link)
        file_name = file_name.split('/')[-1].split('=')[-1]
        file_ext = file_ext if file_ext else '.jpg'
        img_save_path = os.path.join(img_folder_path, file_name+file_ext)

        try:
            urlretrieve(img_link, img_save_path)
            self.ctgr_imgs_count[ctgr] += 1
        except Exception as e:
            print(f'Save failed: {img_link} / Error: {e}')
            logging.warning(f'Save failed: {img_link} / Error: {e}')
            return
        
        mime_type = magic.from_file(img_save_path, mime=True).split('/')[-1]
        if file_ext != mime_type:
            new_file_path = os.path.splitext(img_save_path)[0]+'.'+mime_type
            os.rename(img_save_path, new_file_path)
            img_save_path = new_file_path

        # if index == 0:
        #     main_item_image = True
        # else:
        #     main_item_image = False

        # with open(f'{self.tsv_file_name}.tsv', 'at') as tsv_file: # .tsv 파일 생성
        #     writer = csv.writer(tsv_file, delimiter='\t')
        #     writer.writerow([self.mall, item_name, img_save_path[self.path_index:], main_item_image])
        
    def get_sumnail_image(self, item_link, main_ctgr, sub_ctgr):
        if 'http' in item_link:
            url_link = item_link
        

        self.browser_control(url_link, 'div.sc-is7q9v-0.gTpvXT')
           
        time.sleep(3)
        # 상품 상세 이미지 추출
        try: 
            self.page_scrolldown2bottom()
            img_elements = self.browser.find_elements(By.CSS_SELECTOR,'div.sc-is7q9v-8.kmoZgf img')            
            img_lists = [img.get_attribute('src') for img in img_elements]
                 
        except Exception as e:
            print('상품 상세 이미지 추출 에러',e)

        # 상품 상세 정보 추출
        try : 

            # 상품 명 추출
            error = '상품명'
            product_name_element = self.browser.find_element(By.CSS_SELECTOR,'div.sc-1pxf5ii-0.ixVbGB h2')
            product_name = change_word(product_name_element.text)
            
            # 브랜드 추출
            error = '브랜드'
            brand_element = self.browser.find_element(By.CSS_SELECTOR, 'dd.sc-18j0po5-4.fedfUS a')
            brand_name = change_word(brand_element.text)

            # 성별 추출
            error = '성별'
            sex_element = self.browser.find_elements(By.CSS_SELECTOR,'dd.sc-18j0po5-4.fedfUS span')
            sex_list = ['여성', '남성', '여성, 남성','남성, 여성', '라이프']
            sex_info = [case.text for case in sex_element if case.text in sex_list][0]
            if sex_info not in ['여성','남성']:
                sex_info = '혼성'
            
        except Exception as e:
            print(f'{error} 부분 에러 {e}')
            if error == '성별':
                sex_info = '혼성'
            else:
                return


        # 상품 이미지 저장
        if len(img_lists) >= 1:
            img_folder_path = self.make_save_folder(main_ctgr, sub_ctgr, brand_name , sex_info, product_name)
            
            for index, img_info in enumerate(img_lists):
                self.download_sumnail_image(img_folder_path, product_name, img_info, index, sub_ctgr)
        else:
            return

    def do_crawling(self, ctgr_dict):
        # 무신사 카테고리별 크롤링
        
        for main_ctgr, ctgr_info in ctgr_dict.items():
            for sub_ctgr, ctgr_id in ctgr_info.items():

                # 페이지 로딩
                print(f'Crawling  {main_ctgr} : {sub_ctgr} - Start crawling ....')
                logging.info(f'Crawling  {main_ctgr} : {sub_ctgr} - Start crawling ....')
                main_link = f'https://www.musinsa.com/categories/item/{ctgr_id}?device=mw'

                # 페이지 로딩
                self.browser_control(main_link, 'section.category__sc-1x1c1sb-0.fnCtEX')

                # 무신사 상품 리스트 추출                    
                time.sleep(2)
                full_item_list = OrderedSet()
                last_height = self.browser.execute_script("return document.body.scrollHeight") #초기 스크롤 길이 측정

                while True :
                    # 간격 스크롤 후 아이템 리스트 추가                        
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);") # 스크롤 내림
                    time.sleep(2)
                    new_height = self.browser.execute_script("return document.body.scrollHeight") # 스크롤 내린 후의 스크롤 길이
                    # 상품 수집
                    try:
                        item_element = self.browser.find_elements(By.CSS_SELECTOR,'div.category__sc-rb2kzk-5.hWLdIX figure a')
                        item_list = [element.get_attribute('href') for element in item_element]
                        full_item_list.update(item_list)
                    
                    # 다음 페이지가 존재하지 않는 경우 카테고리 크롤링 종료
                    except Exception as e:
                        print(f'Page error: {e} ')
                        logging.error(f'Page error: {e}')
                        break
                    
                    # 상품 리스트가 존재하지 않는 경우 카테고리 크롤링 종료
                    if not item_list:
                        print(f'Item not found')
                        logging.error(f'Item not found')
                        break
                    
                    if new_height == last_height:
                        break  # 더 이상 스크롤할 페이지가 없을 때
                    last_height = new_height  # 새로운 높이를 이전 높이로 업데이트

                    if self.testing:
                        break # 테스트용 break
                
                full_item_list = full_item_list.to_list()
                ## test 세팅
                if self.testing:
                    full_item_list = full_item_list[:2]
                
                
                # 학습 이미지 크롤링
                for idx in tqdm(range(len(full_item_list))):
                    tqdm.write(f'{sub_ctgr} {idx+1} 번째 상품 crawling 중 : {full_item_list[idx]}')                       

                    self.get_sumnail_image(full_item_list[idx], main_ctgr, sub_ctgr)
                            
        # 카테고리 정보 저장
        ctgr_info_file_name = os.path.join(self.save_path, f'{self.mall}_카테고리_{get_current_time()}.tsv')
        file_exists = os.path.isfile(ctgr_info_file_name)
        with open(f'{ctgr_info_file_name}', 'a',newline='') as ctgr_info_file:
            writer = csv.writer(ctgr_info_file, delimiter='\t')

            if not file_exists:
                writer.writerow(['main_ctgr','sub_ctgr', 'product_count', 'imgs_count', 'time'])

            for (ctgr_info, items_count),(_,imgs_count) in zip(sorted(self.ctgr_items_count.items()),sorted(self.ctgr_imgs_count.items())):
                writer.writerow([main_ctgr, ctgr_info, items_count, imgs_count, get_current_timenow()])

import os, os.path as osp
SAVE_PATH = osp.join(os.getcwd(), 'save')										
DRIBER_PATH = osp.join(os.getcwd(), 'selenium_driver', 'chromedriver')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delete same image of crawling images.')
    parser.add_argument('--mall', type=str, default='Musinsa_mobile', metavar='SHOPPING_MALL',
                        help='Target shopping mall name')
    parser.add_argument('--save-path', type=str, default=SAVE_PATH, metavar='DIR_PATH',
                        help='Directory path to save crawling images')
    parser.add_argument('--driver-path', type=str, default=DRIBER_PATH, metavar='DIR_PATH',
                        help='Directory path to saved chrome driver files')
    parser.add_argument('--test', type=bool, default= False,
                        help='testing or not')
    args = parser.parse_args()

    if not os.path.isdir(args.save_path):
        os.mkdir(args.save_path)

    # 카테고리 크롤링

    crawling_list = {
                    '하의' : {'레깅스':'003005', '숏팬츠':'003009'},
                    '신발' : {'구두':'005014', '로퍼':'005015','힐_펌프스': '005012','플랫슈즈':'005017','블로퍼':'005019',
                                '샌들':'005004','슬리퍼':'005018','기타신발':'005006','모카신_보트':'005016','부츠':'005011'},
                    '스니커즈' : {'캔버스_단화':'018002','패션스니커즈화':'018003','스포츠스니커즈':'018001','기타스니커즈':'018004'},
                    '치마' : {'미니스커트' : '022001'},
                    '속옷' : {'여성속옷상의':'026001','여성속옷하의':'026002','여성속옷세트':'026003','남성속옷':'026004'}

    }

    # 브랜드 리스트 파일 경로 설정
    # 파일이 존재하는지 확인하고, 존재한다면 파일의 내용을 리스트로 변환
    crawler = Crawler(args.mall, args.save_path, args.driver_path, args.test)
    crawler.do_crawling(crawling_list)
    
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

