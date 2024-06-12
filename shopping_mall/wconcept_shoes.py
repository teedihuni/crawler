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


'''
20240601에 진행된 크롤링

wconcept 신발만 수집하는 코드
'''

PROJECT_FOLDER_PATH = './'
sys.path.append(PROJECT_FOLDER_PATH)
from utils import *
from selenium_driver.selenium_init import *

logging.basicConfig(
    level=logging.INFO, # level=logging.DEBUG,
    filename='./save/log/wconcept_shoes.log',
    format="%(asctime)s:%(levelname)s:%(message)s"
)
logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, mall, save_path, driver_path):
        self.base_url = 'https://display.wconcept.co.kr/category' 
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
        
        img_folder_path = os.path.join(self.save_path, self.mall, '신발', main_ctgr, sub_ctgr, change_word(brand_name) , sex, change_word(item_name))
        os.makedirs(img_folder_path, exist_ok=True)
        self.ctgr_items_count[sub_ctgr] += 1  
        
        return img_folder_path

    def download_sumnail_image(self, ctgr_info ,img_folder_path, item_name, img_info, downloaded_imglist):
        
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
                self.ctgr_imgs_count[ctgr_info] +=1
                
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
            
        
    def get_sumnail_image(self, sex):
        # if 'http' in item_link:
        #     url_link = item_link

        # # 내부 상품 페이지 진입
        # self.browser_control(url_link, 'div.pdt_detail')            

        # 이미지 추출
        time.sleep(2)
        try: 
            final_img_links = []
            
            img_container_case1 = self.browser.find_elements(By.CSS_SELECTOR, 'div.marketing img')
            final_img_links.extend([img.get_attribute('src') for img in img_container_case1])

            img_container_case2 = self.browser.find_elements(By.CSS_SELECTOR, 'div.product_sec_textarea.product_textarea img')
            final_img_links.extend([img.get_attribute('src') for img in img_container_case2])

        except Exception as e:
            print(f'썸네일 정보 추출 에러 : {e}')
            final_img_links = []
                

        # 상품명 & 브랜드 명 추출
        try :
            item_name_element = self.browser.find_element(By.CSS_SELECTOR, 'div.h_group div h3')
            item_name = item_name_element.text
            
            brand_name_element = self.browser.find_element(By.CSS_SELECTOR,'div.h_group h2 a')
            brand_name = brand_name_element.text
            
            ctgr_depth_3 = self.browser.find_element(By.ID, 'cateDepth3')
            ctgr_depth_3 = ctgr_depth_3.text
            
            ctgr_depth_4 = self.browser.find_element(By.ID, 'cateDepth4')
            ctgr_depth_4 = ctgr_depth_4.text

        except Exception as e:
            print(f'이름 추출 에러 : {e}')
        

        # 상품 이미지 저장
        try: 
            if len(final_img_links) >= 1:
                img_folder_path = self.make_save_folder(ctgr_depth_3, ctgr_depth_4, brand_name, sex, item_name)
                downloaded_imglist = [os.path.splitext(path)[0] for path in os.listdir(img_folder_path)] 
                for img_info in final_img_links:
                    self.download_sumnail_image(f'{ctgr_depth_3}/{ctgr_depth_4}' ,img_folder_path, item_name, img_info, downloaded_imglist)
            else:
                print('상품이미지가 없음')
        except Exception as e:
            print(f'상품 이미지 저장 에러 : {e}')
            logging.info(f'상품 이미지 저장 에러 : {e}')

        product_info = f'{ctgr_depth_3}/{ctgr_depth_4}/{brand_name}/{sex}/{item_name}'
        return product_info
        

    def do_crawling(self):
        # 29CM 카테고리별 크롤링

        sex_dict = {'women':'여성','men':'남성'}
            
        for sex_key, sex in sex_dict.items():
            page_num = 1 # 페이지 번호
            page_url = '' # 상품 리스트 페이지 URL           

            while True:

                main_page_url = f'{self.base_url}/{sex_key}/002?page={page_num}'

                # 카테고리별 페이지 로드
                self.browser_control(main_page_url, 'div.sc-pieeex-0.kZRWfa.items-grid.list')
                print(f'Crawling category | {sex} - Start page {page_num} ....')
                logging.info(f'Crawling category | {sex} - Start page {page_num} ....')
                time.sleep(2)
                # 상품 리스트 추출
                try:
                    product_boxs = self.browser.find_elements(By.CSS_SELECTOR,'span.sc-1oykv4u-0.crIesh.img.dim-blckTrns003')

                    
                # 다음 페이지가 존재하지 않는 경우 카테고리 크롤링 종료
                except Exception as e:
                    print(f'Page not found: {e} / URL: {page_url}')
                    logging.error(f'Page not found: {e} / URL: {page_url}')
                    break
                
                # 상품 리스트가 존재하지 않는 경우 카테고리 크롤링 종료
                if not product_boxs:
                    print(f'Item not found - URL: {page_url}')
                    logging.error(f'Item not found - URL: {page_url}')
                    break
                    
                # test 세팅
                test_num = 3
                if page_num == 3:
                    break

                # 학습 이미지 크롤링                
                for idx in tqdm(range(len(product_boxs)), desc='진행중'):            
                    self.browser_control(main_page_url, 'div.sc-pieeex-0.kZRWfa.items-grid.list')
                    
                    try:
                        product_boxs = self.browser.find_elements(By.CSS_SELECTOR,'span.sc-1oykv4u-0.crIesh.img.dim-blckTrns003')

                    # 다음 페이지가 존재하지 않는 경우 카테고리 크롤링 종료
                    except Exception as e:
                        print(f'Page not found: {e} / URL: {page_url}')
                        logging.error(f'Page not found: {e} / URL: {page_url}')
                        break
                    
                    self.browser.execute_script("arguments[0].click();", product_boxs[idx])
                    #time.sleep(1)
                    product_info = self.get_sumnail_image(sex)
                    
                    tqdm.write(f'{page_num} page | {idx} 번째 상품 | {product_info} - 크롤링 중')
                    logging.info(f'{page_num} page | {idx} 번째 상품 | {product_info} - 크롤링 중')

                    if idx == test_num:
                        break                                

                page_num += 1

            #category_exit_msg_v2(sub_ctgr, page_num , self.ctgr_items_count, self.ctgr_imgs_count)
            #os.rename(f'{self.tsv_file_name}.tsv', f'{self.tsv_file_name}_{get_current_time()}.tsv') # .tsv 파일명 변경
                
        # 카테고리 정보 저장
        ctgr_info_file_name = os.path.join(self.save_path, f'{self.mall}/카테고리_{get_current_time()}.tsv')
        with open(f'{ctgr_info_file_name}.tsv', 'wt') as ctgr_info_file:
            writer = csv.writer(ctgr_info_file, delimiter='\t')
            writer.writerow(['category', 'product_count','image_count'])
            for (ctgr_info, product_count),(_, image_count) in zip(sorted(self.ctgr_items_count.items()),sorted(self.ctgr_imgs_count.items())):

                writer.writerow([ctgr_info, product_count, image_count])
                
import os, os.path as osp
SAVE_PATH = osp.join(os.getcwd(), 'save')						
DRIBER_PATH = osp.join(os.getcwd(), 'selenium_driver', 'chromedriver')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delete same image of crawling images.')
    parser.add_argument('--mall', type=str, default='wconcept', metavar='SHOPPING_MALL',
                        help='Target shopping mall name')
    parser.add_argument('--save-path', type=str, default=SAVE_PATH, metavar='DIR_PATH',
                        help='Directory path to save crawling images')
    parser.add_argument('--driver-path', type=str, default=DRIBER_PATH, metavar='DIR_PATH',
                        help='Directory path to saved chrome driver files')
    args = parser.parse_args()

    if not os.path.isdir(f'{args.save_path}/{args.mall}'):
        os.mkdir(f'{args.save_path}/{args.mall}')


    crawler = Crawler(args.mall, args.save_path, args.driver_path)
    crawler.do_crawling()
    
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

