import os
from tqdm import tqdm

def count_images_in_folder(folder_path):
    image_extensions = {'.jpg', '.jpeg', '.png'}
    image_count = 0

    # 폴더 내의 모든 파일과 폴더를 순회
    for entry in os.listdir(folder_path):
        # 완전한 경로를 얻기
        full_path = os.path.join(folder_path, entry)
        # 파일이고 이미지 확장자를 가지면 카운트 증가
        if os.path.isfile(full_path) and os.path.splitext(full_path)[1].lower() in image_extensions:
            image_count += 1

    return image_count

def cnt_product(path):
    product_list = os.listdir(path)
    product_num = len(product_list)
    
    return product_num

# 카테고리 폴더 경로 예시: '/path/to/category'
category_path = '/home/crawling/crawling/crawling_img_save/crawling/W_concept_full'

mall_list  = os.listdir(category_path)
type_1 = ['Plural','Single']
type_2 = ['상의/아우터','하의/데님','하의/바지','하의/치마']

prouduct_count_dic = { f'{tp}' : 0 for tp in type_2 }
image_count_dic = { f'{tp}' : 0 for tp in type_2 }


for idx , mall in tqdm(enumerate(mall_list)):
    #print(mall)
    for tp_1 in type_1:
            for tp_2 in type_2:
                mall_path = f"{category_path}/{mall}/{tp_1}/{tp_2}"
                
                try : 
                    cnt = cnt_product(mall_path)
                    prouduct_count_dic[tp_2]+=cnt
                    
                except Exception as e:
                    continue
                
                try :
                    product_list = os.listdir(mall_path)
                    for product in product_list:
                        path  = f"{mall_path}/{product}"
                        image_num = count_images_in_folder(path)
                        image_count_dic[tp_2] += image_num
                        
                except Exception as e:
                    continue
                        
                
                
    # if idx == 1:
    #     break

print(prouduct_count_dic)
print(image_count_dic)
                
                

