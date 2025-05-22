from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait         # ← 추가
from selenium.webdriver.support import expected_conditions as EC

import time
import pymysql
import re

# 상품명 정제 함수
def clean_product_name(name):
    # 괄호와 그 안의 내용 제거
    cleaned = re.sub(r'\([^)]*\)', '', name)
    # 대괄호와 그 안의 내용 제거
    cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)
    # 불필요한 공백 제거
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 숫자와 단위 조합만 제거 (예: "1봉", "2봉", "봉/팩" 등)
    cleaned = re.sub(r'(\d+~?\d*|~?\d+)?\s*(kg|g|입|박스|통|내외|개|ml|ML|L|포|캔|병|장|롤|매|호|세트|set|Pack|EA|입수|미만|망|/호|/팩|/봉|/박스|/통|/개|/망|/포|/캔|/병|/장|/롤|/매|/세트|/set|/Pack|/EA|/입수)?', '', cleaned)
    
    # / 뒤에 오는 단위 제거
    cleaned = re.sub(r'/\s*(kg|g|입|박스|통|내외|개|ml|ML|L|포|캔|병|장|롤|매|세트|set|Pack|EA|입수|미만|망|cm)', '', cleaned)
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

print("크롬드라이버 실행")
service = Service('C:/Users/User/paddle_ocr_test/my-ocr-app/chromedriver.exe')
driver = webdriver.Chrome(service=service)
driver.get('https://emart.ssg.com/disp/category.ssg?dispCtgId=6000228036')
time.sleep(3)

all_ingredients = set()  # 중복 방지용 set

for page in range(1,20):  # 1~
    print(f"{page}페이지 크롤링 중...")
    time.sleep(2)
    elements = driver.find_elements(By.CLASS_NAME, 'mnemitem_goods_tit')
    page_ingredients = [clean_product_name(el.text.strip()) for el in elements if el.text.strip()]
    all_ingredients.update(page_ingredients)    
    print(f"{page}페이지 상품: {page_ingredients}")

    if not page_ingredients:
        print("더 이상 이동할 페이지가 없습니다. 종료.")
        break

    try:
        next_page_num = page + 1
        page_btns = driver.find_elements(By.XPATH, f"//a[text()='{next_page_num}']")
        if page_btns:
            driver.execute_script("arguments[0].click();", page_btns[0])
            # 페이지 이동 후 대기
            WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'mnemitem_goods_tit'))
            )
        else:
            # 페이지 번호가 없으면 오른쪽 화살표(>) 클릭
            next_btns = driver.find_elements(By.CLASS_NAME, 'btn_next')
            if next_btns:
                driver.execute_script("arguments[0].click();", next_btns[0])
                WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'mnemitem_goods_tit'))
                )
            else:
                print("더 이상 이동할 페이지가 없습니다. 종료.")
                break      
    except Exception as e:
        print(f"{page+1}페이지 버튼 클릭 실패: {e}")
        break

driver.quit()
print("드라이버 종료")

# === 여기서부터 DB 저장 ===
conn = pymysql.connect(
    host='localhost',
    user='noname',         # ← 본인 MySQL 계정
    password='noname', # ← 본인 MySQL 비번
    db='refrige_go',             # ← 본인 DB명
    charset='utf8'
)
cursor = conn.cursor()
for name in all_ingredients:
    cleaned_name = clean_product_name(name)
    cursor.execute("INSERT IGNORE INTO ai_ingredients (ai_ingredient_name) VALUES (%s)", (cleaned_name,))
conn.commit()
conn.close()
print("DB 저장 완료")