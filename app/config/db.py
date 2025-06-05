import os
import pymysql

def find_in_database(word: str):
    print("실제 접속 DB 정보:", os.getenv('DB_HOST'), os.getenv('DB_PORT'), os.getenv('DB_NAME'), os.getenv('DB_USER'))
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST', 'refrige-go-db.c9qa8oew47ux.ap-northeast-2.rds.amazonaws.com'),
            port=int(os.getenv('DB_PORT', 3306)),
            db=os.getenv('DB_NAME', 'refrige_go'),
            user=os.getenv('DB_USER', 'nonameteam'),
            password=os.getenv('DB_PASSWORD', 'nonameteam'),
            charset='utf8'
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT DATABASE();")
            print("실제 접속된 DB:", cursor.fetchone())
            sql = "SELECT id, name FROM ingredients WHERE name=%s"
            cursor.execute(sql, (word,))
            result = cursor.fetchone()
        conn.close()
        if result:
            # 예시: id, name만 반환 (confidence, alternatives는 필요시 추가)
            return type('Ingredient', (), {
                "id": result[0],
                "name": result[1],
                "confidence": 1.0,
                "alternatives": []
            })()
        return None
    except Exception as e:
        print("DB 조회 실패:", e)
        return None