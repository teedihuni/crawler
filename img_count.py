import os
from collections import defaultdict

# 카테고리 폴더 경로 예시: '/path/to/category'
#category_path = '/home/crawling/hdd/shopping_mall_crawler/save/'
main_path = '/home/crawling/crawling/crawling_img_save/save'
mall_list = os.listdir(main_path)
except_mall = ['Musinsa','logs','29cm']
ctgr_list = ['아우터','하의','치마']

#mall_list = ['NEXT']

mall_cnt_dict = dict()

for mall in mall_list:
    ctgr_dict = dict()
    if mall not in except_mall:
        print(f"Counting {mall}")
        for ctgr in ctgr_list :
            try :
                category_path = os.path.join(main_path,mall,ctgr)
                product_list = os.listdir(category_path)
                
                product_count = len(product_list)
                img_counts = 0 
                
                for product in product_list:
                    img_path = os.path.join(category_path,product)
                    for img in os.listdir(img_path):
                        if img.lower().endswith(('.png', '.jpg', '.jpeg')):
                            img_counts+=1
                                 
            except Exception as e:
                pass
            
            ctgr_dict[ctgr] = f"[상품 수  {product_count}, 이미지 수 {img_counts}]"
    
        mall_cnt_dict[mall]  = ctgr_dict
    

for key, value in mall_cnt_dict.items():
    print(key, value)

