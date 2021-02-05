import mysql.connector
import time

class MySQLDataWriter:
    def __init__(self):
        self.db_connection=mysql.connector.connect(
            user='ffml',
            host='82.156.53.167',
            database='ffml_test',
            password='ffml123456',
        )
        self.cursor=self.db_connection.cursor()

    def execute(self,sql,data):
        self.cursor.execute(sql,data)
        return self.cursor

    def commit(self):
        self.db_connection.commit()

    def close(self):
        self.cursor.close()
        self.db_connection.close()

if __name__ == '__main__':
    db=MySQLDataWriter()
    query = "INSERT INTO badaccount(accountnumber) VALUES (%s);"
    data=[]
    for id in range(100000):
        data.append(tuple([id]))

    begin=time.time()
    db.cursor.executemany(query,data)
    db.commit()
    print(f"Running time: {time.time()-begin}")


    db.close()
