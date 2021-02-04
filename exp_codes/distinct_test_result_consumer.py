from collections import defaultdict

from kafka import KafkaConsumer
import json,threading,time
from statistics import mean
from datetime import datetime,timedelta
from influxdb import InfluxDBClient

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

BOOTSTRAP_SERVERS = ['10.0.0.13:9092']
#TOPIC="alert"
#MEASUREMENT="ffml.latency"
#WRITE_INFLUXDB=True

#BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC="distinct_test"
#MEASUREMENT="distinct.latency"
WRITE_INFLUXDB=False

consumer = KafkaConsumer(TOPIC,
                         #auto_offset_reset='earliest',
                         enable_auto_commit=False,
                             group_id='test-group',
                             bootstrap_servers=BOOTSTRAP_SERVERS,
                             value_deserializer=lambda m: json.loads(m.decode('utf-8')))

if WRITE_INFLUXDB:
    client = InfluxDBClient(host="10.0.0.11", port=8086, database='mydb')

records_sum=0
total_latency=0


max_time=datetime(2020,1,1,1,1,1)
def get_max_proc_time():
    global max_time,records_sum,send_token
    id_count=defaultdict(int)
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`

        #print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
        #                                     message.offset, message.key,
        #                                     message.value))

        if message.value['state']:
            records_sum += 1
            cnt=int(message.value['count'])
            id_count[cnt]+=1
            if id_count[cnt]>2:
                print(cnt)
            result_dt = datetime.strptime(message.value['resulttime'], TIME_FORMAT)
            #latency = (result_dt - source_dt)/timedelta(milliseconds=1)
            if result_dt>max_time:
                max_time=result_dt
            #if send_token:
            #    send_token=False
            #    print(records_sum)


def get_total_proc_time():
    global send_token, records_sum,total_latency
    source_dt=None
    #total_latency=0
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`

        #print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
        #                                     message.offset, message.key,
        #                                     message.value))

        if message.value['state']:
            records_sum += 1
            if source_dt is None:
                source_dt = datetime.strptime(message.value['resulttime'], TIME_FORMAT)
                print(source_dt)
            else:
                result_dt = datetime.strptime(message.value['resulttime'], TIME_FORMAT)
                latency = (result_dt - source_dt)/timedelta(milliseconds=1)
                if latency>0:
                    source_dt=result_dt
                    print(latency)
                    total_latency+=latency
                    #latencies.append(latency / timedelta(milliseconds=1))
                    if send_token:
                        send_token = False
                        #ml = mean(latencies)
                        print(latency)
                        #latencies = []
                        if WRITE_INFLUXDB:
                            write_influxdb(MEASUREMENT, latency)


def write_influxdb(measurement,value):
    dt=datetime.utcnow()
    json_body = [
        {
            "measurement": measurement,
            "tags": {
                "host": "server01",
                "region": "us-west"
            },
            "time": dt.strftime(TIME_FORMAT),
            "fields": {
                "value": value
            }
        }
    ]
    client.write_points(json_body,retention_policy='one_day')

send_token=False
timer_alive=True

def timer_thread(sec):
    def foo():
        global send_token,timer_alive,records_sum
        next_call = time.time()
        while True and timer_alive:
            send_token=True
            print(f"Consumed {records_sum}")
            next_call = next_call+sec
            time.sleep(next_call - time.time())

    timerThread = threading.Thread(target=foo)
    timerThread.start()

def distinct_thread():
    global records_sum,max_time
    try:
        get_max_proc_time()
    except:
        print(f"Consumed records: {records_sum}")
        print(f"Max time: {max_time.strftime(TIME_FORMAT)}")


def main_thread():
    global timer_alive
    try:
        get_total_proc_time()
        #consume_msg()
    except:
        print(f"Consumed records: {records_sum}")
        print(f"Total latency: {total_latency}")
        timer_alive=False

if __name__ == '__main__':
    #dt=datetime.utcnow()
    #print(dt.strftime(TIME_FORMAT))
    timer_thread(5)
    distinct_thread()

    #timer_thread(10)
    #main_thread()
