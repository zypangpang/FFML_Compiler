from kafka import KafkaConsumer
import json,threading,time
from statistics import mean
from datetime import datetime,timedelta
from influxdb import InfluxDBClient

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
consumer = KafkaConsumer('alert',
                         #auto_offset_reset='earliest',
                         enable_auto_commit=False,
                             group_id='test-group',
                             bootstrap_servers=['10.0.0.13:9092'],
                             value_deserializer=lambda m: json.loads(m.decode('utf-8')))

client = InfluxDBClient(host="10.0.0.11", port=8086, database='mydb')
records_sum=0

def consume_msg():
    latencies=[]
    global send_token,records_sum
    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                              message.offset, message.key,
                                              message.value))
        if message.value['state']:
            records_sum+=1
            source_dt=datetime.strptime(message.value['sourcetime'],TIME_FORMAT)
            result_dt=datetime.strptime(message.value['resulttime'],TIME_FORMAT)
            latency=result_dt-source_dt
            latencies.append(latency/timedelta(milliseconds=1))
            if send_token:
                send_token=False
                ml=mean(latencies)
                print(ml)
                latencies=[]
                write_influxdb(ml)


    # consume earliest available messages, don't commit offsets
    #KafkaConsumer(auto_offset_reset='earliest', enable_auto_commit=False)

    # StopIteration if no message after 1sec
    #KafkaConsumer(consumer_timeout_ms=1000)



def write_influxdb(value):
    dt=datetime.utcnow()
    json_body = [
        {
            "measurement": "ffml.latency",
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
    client.write_points(json_body)

send_token=False
timer_alive=True

def timer_thread(sec):
    def foo():
        global send_token,timer_alive
        next_call = time.time()
        while True and timer_alive:
            send_token=True
            next_call = next_call+sec
            time.sleep(next_call - time.time())

    timerThread = threading.Thread(target=foo)
    timerThread.start()

def main_thread():
    global timer_alive
    try:
        consume_msg()
    except:
        print(f"Consumed records: {records_sum}")
        timer_alive=False

if __name__ == '__main__':
    #dt=datetime.utcnow()
    #print(dt.strftime(TIME_FORMAT))
    timer_thread(10)
    main_thread()
