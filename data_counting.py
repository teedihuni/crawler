
import os
from collections import defaultdict
import pandas

path = '/home/crawling/crawling/crawling_img_save/MR_PORTER'
shoppling_mall = path.split('/')[-1]

# 각 쇼핑몰에 대한 카테고리별 정보를 저장할 통합된 딕셔너리
mall_info = defaultdict(lambda: defaultdict(lambda: {'image_count': 0, 'product_count': 0}))

for root, dirs, files in os.walk(path):
    parts = root.split('/')
    if parts[-4] == shoppling_mall:
        

        category = parts[-2]
        mall_name = parts[-3]

        # 현재 쇼핑몰과 카테고리에 대한 이미지 개수와 상품 개수 업데이트
        mall_info[mall_name][category]['image_count'] += len(files)
        mall_info[mall_name][category]['product_count'] += 1

# 결과 출력
import pandas as pd

data = []
for mall, categories in mall_info.items():
    row = {'mall': mall}
    for category, counts in categories.items():
        row[f'{category} images'] = counts['image_count']
        row[f'{category} products'] = counts['product_count']
    data.append(row)


# 리스트를 DataFrame으로 변환
df = pd.DataFrame(data)

# Excel 파일로 저장
df.to_excel(f'/home/crawling/crawling/{shoppling_mall}_counts.xlsx', index=False)
