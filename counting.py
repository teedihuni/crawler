from collections import defaultdict
import os

'''
새로 crawling 하는 무신사, wconcept, 29cm 결과물에 대해서 이미지와 상품수 카운팅코드
'''

#신발은 세부 depth가 있어서 경로설정을 하나 아래로 적용
main_path = '/home/dhlee2/workspace/crawling_code/shopping_mall_crawler/save/Musinsa_mobile'
# main_path = '/home/dhlee2/workspace/crawling_code/shopping_mall_crawler/save/wconcept/신발'
main_path ='/home/dhlee2/workspace/crawling_code/shopping_mall_crawler/save/29cm/신발'

count_info = defaultdict(list)

main_ctgr_list = os.listdir(main_path)
sex_case = ['여성','남성','혼성']
exe = ['.jpg','.jpeg','.png']

for main_ctgr in main_ctgr_list:
    depth_1_path = os.path.join(main_path, main_ctgr)
    sub_ctgr_list = os.listdir(depth_1_path)
    sub_ctgr_dict = dict()
    for sub_ctgr in sub_ctgr_list:
        pr_counts = 0
        img_counts = 0
        depth_2_path = os.path.join(depth_1_path, sub_ctgr)
        brand_list = os.listdir(depth_2_path)


        for brand in brand_list:
            for sex in sex_case:
                sub_path = os.path.join(depth_2_path, brand, sex)
                try:
                    product_list = os.listdir(sub_path)
                    pr_counts += len(product_list)
                except:
                    continue

                for product in product_list :
                    img_path = os.path.join(sub_path, product)
                    img_list = [img for img in os.listdir(img_path) if os.path.splitext(img)[-1] in exe]
                    img_counts += len(img_list)
        
        sub_ctgr_dict[sub_ctgr] = {            
                '상품 개수' : pr_counts,
                '이미지 개수' : img_counts
            }
    count_info[main_ctgr].append(sub_ctgr_dict)

#print(count_info)

if main_path.split('/')[-1] == '신발':
    print('==========================================')
    print('상위카테고리 : 신발')
    print('==========================================')

for key, value in count_info.items():
    print('------------------------------------------')
    print(key)
    for sub_key, sub_value in value[0].items():
        print(sub_key, sub_value)
