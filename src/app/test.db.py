import pymysql

try:
    print("DB 연결 시도")
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        db='refrige_go',
        user='noname',
        password='noname',
        charset='utf8'
    )
    print("DB 연결 성공")
    conn.close()
except Exception as e:
    print("DB 연결 실패:", e)