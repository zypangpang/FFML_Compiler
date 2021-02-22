import csv

import mysql.connector
import time

from common import FileManager


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

def insert_badaccount(db):
    query = "INSERT INTO badaccount(accountnumber) VALUES (%s);"
    data = []
    for id in range(100000):
        data.append(tuple([id]))

    begin = time.time()
    db.cursor.executemany(query, data)
    db.commit()
    print(f"Running time: {time.time() - begin}")

def insert_usualip(db):
    query = "INSERT INTO usualip(accountnumber,ip) VALUES (%s,%s);"
    data = []
    ip="188.188.188.188"
    for id in range(100000):
        data.append((id,ip))

    begin = time.time()
    db.cursor.executemany(query, data)
    db.commit()
    print(f"Running time: {time.time() - begin}")

def insert_usualdid(db):
    query = "INSERT INTO usualdeviceid(accountnumber,did) VALUES (%s,%s);"
    data = []
    did=2021
    for id in range(100000):
        data.append((id,did))

    begin = time.time()
    db.cursor.executemany(query, data)
    db.commit()
    print(f"Running time: {time.time() - begin}")

def insert_singlelimit(db):
    query = "INSERT INTO singlelimit(accountnumber,singlelimit) VALUES (%s,%s);"
    data = []
    singlelimit=1000
    for id in range(100000):
        data.append((id,singlelimit))

    begin = time.time()
    db.cursor.executemany(query, data)
    db.commit()
    print(f"Running time: {time.time() - begin}")

def insert_transcount(db):
    with open(FileManager.get_path("agg_transcount"),'r') as file:
        reader=csv.reader(file)
        next(reader)

        query = "INSERT INTO ONL_transcount(accountnumber,transcount,`date`) VALUES (%s,%s,%s);"
        begin = time.time()
        db.cursor.executemany(query, reader)
        db.commit()
        print(f"Running time: {time.time() - begin}")

def insert_totaldebit(db):
    with open(FileManager.get_path("agg_totaldebit"),'r') as file:
        reader=csv.reader(file)
        next(reader)

        query = "INSERT INTO ONL_totaldebit(accountnumber,totaldebit,`date`) VALUES (%s,%s,%s);"
        begin = time.time()
        db.cursor.executemany(query, reader)
        db.commit()
        print(f"Running time: {time.time() - begin}")


if __name__ == '__main__':
    db = MySQLDataWriter()
    #insert_badaccount(db)
    #insert_usualip(db)
    #insert_usualdid(db)
    #insert_singlelimit(db)
    insert_totaldebit(db)
    db.close()
