# Shopping mall crawler

쇼핑몰에서 상품 내부 이미지를 수집

* 쇼핑몰 리스트
    - 일부 쇼핑몰은 특정 카테고리 수집을 위해서 해당 카테고리만을 위한 수집코드를 작성
    - 카테고리마다 url주소와 변하는 값의 위치가 다르고 페이지 형태나 선택자가 달라지는 경우에는 별도의 코드로 구성함

1. 29cm
    - base
    - shoes
2. musinsa_mobile
    - base
    - swimming
    - onepiece
3. wconcept
    - clothes
    - shoes
4. SSFSHOP


### initial setting

```
conda create -n crawler python=3.9.12
pip install -r requirements.py
```


## start
* 수집하고자 하는 상품의 코드 및 상위 카테고리 코드 확인 후 __main__ 부분에 dictionary 삽입
* save directory 혹은 log save directory는 적절히 수정


## issues
1. musinsa mobile
    - 2024 6월 부터 무신사 pc페이지를 모두 모바일 형태로 변경
    - 상품 로딩이 page방식가 아닌 무한스크롤로 이루어져있음

2. browser control
    - 수집 중간에 중단되버리는 경우 chrome driver 재시작 

3. page_scrolldown2bottom
    - 스크롤 내리기
    - 일부 웹사이트들은 페이지를 내려야 html 로딩이 되는 경우가 있음


## 크롤링 완료된 후
일반적인 저장 경로 : 
하의 > 쇼트 > 브랜드 > 성별 > 상품명 > 이미지
1. main_counting.py
    - 위의 경로대로 수집된 상품, 이미지 수를 출력




    

    
