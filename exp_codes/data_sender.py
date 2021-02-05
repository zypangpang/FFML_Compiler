import threading

from common import FileManager,KafkaEventWriter
import time,csv,sys

class DataSender:

    def __init__(self,event_writer):
        self.event_writer=event_writer
        self.event_file = open(FileManager.get_path('events'), 'r')
        self.transfer_file = open(FileManager.get_path('transfer'), 'r')
        self.event_reader = csv.DictReader(self.event_file)
        self.transfer_reader = csv.DictReader(self.transfer_file)

    def send_event_transfer(self,num):
        #sleep_sec=1/freq
        id=0
        try:
            #while True:
            for _ in range(num):
                #if num>0 and id>=num:
                #    break
                #time.sleep(sleep_sec)
                cur_event=self.event_reader.__next__()
                cur_event['id']=int(cur_event['id'])
                cur_event['accountnumber']=int(cur_event['accountnumber'])
                #print(cur_event)
                self.event_writer.write_event(cur_event)
                if cur_event['eventtype']=='transfer':
                    transfer_event=self.transfer_reader.__next__()
                    transfer_event['id'] = int(transfer_event['id'])
                    transfer_event['accountnumber'] = int(transfer_event['accountnumber'])
                    transfer_event['dest_accountnumber'] = int(transfer_event['dest_accountnumber'])
                    #print(transfer_event)
                    #transfer_event['id']=int(transfer_event['id'])
                    #transfer_event['accountnumber']=int(transfer_event['accountnumber'])
                    #transfer_event['value']=float(transfer_event['value'])
                    self.event_writer.write_transfer(transfer_event)
            #    id+=1
        except Exception as e:
            print(e)

    def close(self):
        self.event_file.close()
        self.transfer_file.close()

def send_data(interval_span,records_per_interval,rounds):
    # change interval_span to seconds
    interval_span/=1000
    round_cnt=0
    writer = KafkaEventWriter()
    sender = DataSender(writer)

    def run():
        next_call=time.time()
        sender.send_event_transfer(records_per_interval)
        nonlocal round_cnt
        round_cnt+=1
        if round_cnt%100==0:
            print(f"Send {records_per_span*round_cnt} records")
        if round_cnt<=rounds:
            next_call=next_call+interval_span
            threading.Timer(next_call-time.time(),run).start()
        else:
            sender.close()

    threading.Timer(interval_span,run).start()

if __name__ == '__main__':
    interval_span=100 # ms 100ms has best precision
    records_per_span=10
    total_records=100000
    try:
        interval_span=int(sys.argv[1])
    except:
        print("Use default span 10 ms ")
    try:
        records_per_span=int(sys.argv[2])
    except:
        print("Use default records per span 20")
    try:
        total_records=int(sys.argv[3])
    except:
        print("total records 100000")
    rounds=int(total_records/records_per_span)

    send_data(interval_span,records_per_span,rounds)
