from kafka import KafkaConsumer
import json,threading,time
from statistics import mean
from datetime import datetime,timedelta
from influxdb import InfluxDBClient

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

#BOOTSTRAP_SERVERS = ['10.0.0.13:9092'],
#TOPIC="alert"
#MEASUREMENT="ffml.latency"
#WRITE_INFLUXDB=True

BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC="distinct_ori"
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
min_time=datetime(2022,1,1,1,1,1)
send_token=False

def get_min_event_time():
    global min_time, records_sum,send_token
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`

        # print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
        #                                     message.offset, message.key,
        #                                     message.value))

        if message.value['state']:
            records_sum += 1
            result_dt = datetime.strptime(message.value['sourcetime'], TIME_FORMAT)
            # latency = (result_dt - source_dt)/timedelta(milliseconds=1)
            if result_dt < min_time:
                min_time = result_dt
            #if send_token:
            #    send_token=False
            #    print(records_sum)


def distinct_thread():
    try:
        get_min_event_time()
    except Exception as e:
        print(e)
    except:
        print(f"Consumed records: {records_sum}")
        print(f"Min time: {min_time.strftime(TIME_FORMAT)}")

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

if __name__ == '__main__':
    timer_thread(5)
    distinct_thread()