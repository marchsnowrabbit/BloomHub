import pymysql
conn = pymysql.connect(host='127.0.0.1', user='root',  password='12345678', db='market_db', charset='utf8')
cur = conn.cursor()

cur.execute("SELECT * FROM member")

print("    멤버id         member이름               주소          맴버 수            phone1")
print("----------------------------------------------------")
while (True) :
    row = cur.fetchone()              
    if row== None :  break
    data1 = row[0]                      
    data2 = row[1]
    data3 = row[2]
    data4 = row[3]
    data5 = row[4]
    print("%10s   %10s   %20s   %10s    %10s" % (data1, data2, data3, data4, data5))

conn.close()