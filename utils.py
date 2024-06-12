import logging
import re
import random
from datetime import date, datetime
from collections import OrderedDict


__all__ = ['get_random_number', 'get_random_number2', 'get_current_time', 'get_current_timenow','change_word', 'change_tsv_name', 
           'category_exit_msg','brand_category_exit_msg','category_exit_msg_v2', 'OrderedSet']
logger = logging.getLogger(__name__)

def get_random_number():
    # 실행 지연 시간
    return random.randint(0, 1)

def get_random_number2():
    # 실행 지연 시간
    return random.randint(2, 3)

def get_current_time():
    # 현재 일자
    return date.today().strftime("%y%m%d")

def get_current_timenow():
    # 현재 시간
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def change_word(word):
    # 특수문자 변경
    pattern = re.compile('[^a-zA-Z0-9ㄱ-ㅣ가-힣]+')
    return re.sub(pattern, '_', word)

def change_tsv_name(word):
    # .tsv 파일을 위한 특수문자 변경
    return word.replace('/', '|').replace(' ', '')


def brand_category_exit_msg(ctgr,brand_name, page_num, plural_ctgr_count, single_ctgr_count):
    print(f'{brand_name} Category {ctgr} finish. Final page: {page_num}.')
    logging.info(f'{brand_name} Category {ctgr} finish. Final page: {page_num}.')
    print(f'{brand_name} Current download items - Plural: {plural_ctgr_count[ctgr]} / Single: {single_ctgr_count[ctgr]}')
    logging.info(f'{brand_name} Current download items - Plural: {plural_ctgr_count[ctgr]} / Single: {single_ctgr_count[ctgr]}')


def category_exit_msg(ctgr, page_num, plural_ctgr_count, single_ctgr_count):
    print(f'Category {ctgr} finish. Final page: {page_num}.')
    logging.info(f'Category {ctgr} finish. Final page: {page_num}.')
    print(f' Current download items - Plural: {plural_ctgr_count[ctgr]} / Single: {single_ctgr_count[ctgr]}')
    logging.info(f'Current download items - Plural: {plural_ctgr_count[ctgr]} / Single: {single_ctgr_count[ctgr]}')
    
def category_exit_msg_v2(ctgr, page_num , ctgr_items_count, ctgr_images_count):
    print(f'Category {ctgr} finish. Final page: {page_num}.')
    logging.info(f'Category {ctgr} finish. Final page: {page_num}.')
    print(f' Current download items - 상품 수 : {ctgr_items_count[ctgr]} / 이미지 수: {ctgr_images_count[ctgr]}')
    logging.info(f'Current download items - 상품 수 : {ctgr_items_count[ctgr]} / 이미지 수: {ctgr_images_count[ctgr]}')

class OrderedSet:
    def __init__(self):
        self.data = OrderedDict()
    
    def update(self, iterable):
        for item in iterable:
            self.data[item] = None
    
    def to_list(self):
        return list(self.data.keys())