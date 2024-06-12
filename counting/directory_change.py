import os
import shutil
from glob import glob

def move_and_delete_subfolders(parent_folder, subfolders):
    # parent_folder 내의 각 subfolder를 처리
    for subfolder in subfolders:
        subfolder_path = os.path.join(parent_folder, subfolder)
        
        # subfolder 내의 각 항목에 대해
        if os.path.isdir(subfolder_path):
            for ctgr in os.listdir(subfolder_path):
                for tp in ['Plural','Single']:
                    brand_path = os.path.join(subfolder_path, ctgr, tp)
                    try: 
                        
                        for item in os.listdir(brand_path):
                            item_path = os.path.join(brand_path, item)
                    
                        # 항목이 디렉토리인 경우, parent_folder로 이동
                            if os.path.isdir(item_path):
                                destination = os.path.join(subfolder_path, ctgr)
                                
                                # 동일한 이름의 폴더가 이미 존재하는 경우 처리
                                shutil.move(item_path, destination)
                                #print(f"Moved {item_path} to {destination}")
                                    
                        # subfolder 삭제
                        shutil.rmtree(brand_path)
                        #print(f"Deleted {brand_path}")
                    except Exception as e:
                        pass
                        #print(e)


def check_directory(path, sub_list):
    ctgr_list = set()

    for brand in sub_list:
        ctgr_path = os.path.join(path, brand)
        if os.path.isdir(ctgr_path):

            for ctgr in os.listdir(ctgr_path):
                ctgr_list.add(ctgr)
    
    return ctgr_list


def change_directory(high_path):
    main_ctgrs = os.listdir(high_path)
    for main_ctgr in main_ctgrs: #상위 카테고리
        main_ctgr_path = os.path.join(high_path , main_ctgr)
        for tp in ['Single','Plural']:
            try : 
                sub_ctgrs = os.listdir(os.path.join(main_ctgr_path, tp))
            except Exception as e :
                continue # tp 존재하지 않는 경우
            
            for sub_ctgr in sub_ctgrs:
                product_list = os.listdir(os.path.join(main_ctgr_path, tp, sub_ctgr)) #상품 리스트
                
                #상품 내 색상 폴더 이슈 해결
                for product in product_list:
                    product_path = os.path.join(main_ctgr_path, tp, sub_ctgr,product)
                    inner_list = os.listdir(product_path)
                    
                    for inner in inner_list :
                        if not any(inner.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']): # 이미지가 아니라 폴더인 경우
                            new_folder_name = f'{product} {inner}'
                            new_product_path = os.path.join(main_ctgr_path, tp, sub_ctgr,new_folder_name)
                            sorce_path = os.path.join(main_ctgr_path, tp, sub_ctgr,product,inner)
                            
                            # 폴더 이동
                            shutil.move(sorce_path,new_product_path)
                            
                #색상 수정된 이후 다시 상품 리스트 추출
                product_list = os.listdir(os.path.join(main_ctgr_path, tp, sub_ctgr))
                for product in product_list:
                    product_path = os.path.join(main_ctgr_path, tp, sub_ctgr,product)
                    target_path = os.path.join(main_ctgr_path, product)
                    
                    # 이동하려는 곳에 폴더가 존재하는 경우
                    if os.path.exists(target_path):
                        counter = 1
                        while os.path.exists(f'{target_path}_{counter}'):
                            counter += 1
                        target_path = f'{target_path} {counter}'
                    
                    shutil.move(product_path, target_path)

def remove_empty_folders(base_dir):
    for root, dirs, files in os.walk(base_dir, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)
                
                
# # 무신사 경로 변경
# parent_folder = '/home/crawling/crawling/crawling_img_save/Musinsa'
# sub_folders = os.listdir(parent_folder)

# ctgr_list = check_directory(parent_folder, sub_folders)
# print(ctgr_list)

# move_and_delete_subfolders(parent_folder, sub_folders)

#===================================


# 무신사, 29cm 이전에 크롤링한 것들 경로 바꾸기

base_dir = '/home/dhlee2/workspace/crawling_code/shopping_mall_crawler/save/EN_aritzia_2'
change_directory(base_dir)
remove_empty_folders(base_dir)




    





