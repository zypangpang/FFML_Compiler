from common import FileManager,KafkaEventWriter
import time,csv,sys

class DataSender:

    def __init__(self,event_writer):
        self.event_writer=event_writer

    def send_event_transfer(self,freq,num=-1):
        sleep_sec=1/freq

        event_file=open(FileManager.get_path('events'),'r')
        transfer_file=open(FileManager.get_path('transfer'),'r')
        event_reader=csv.DictReader(event_file)
        transfer_reader=csv.DictReader(transfer_file)

        id=0
        try:
            while True:
                if num>0 and id>=num:
                    break
                time.sleep(sleep_sec)
                cur_event=event_reader.__next__()
                cur_event['id']=int(cur_event['id'])
                cur_event['accountnumber']=int(cur_event['accountnumber'])
                print(cur_event)
                self.event_writer.write_event(cur_event)
                if cur_event['eventtype']=='transfer':
                    transfer_event=transfer_reader.__next__()
                    print(transfer_event)
                    #transfer_event['id']=int(transfer_event['id'])
                    #transfer_event['accountnumber']=int(transfer_event['accountnumber'])
                    #transfer_event['value']=float(transfer_event['value'])
                    self.event_writer.write_transfer(transfer_event)
                id+=1
        except Exception as e:
            print(e)

        event_file.close()
        transfer_file.close()

if __name__ == '__main__':
    freq=1
    num=-1
    try:
        freq=int(sys.argv[1])
    except:
        print("Use default frequency 1 record/s")
    try:
        num=int(sys.argv[2])
    except:
        print("Send all data")

    writer=KafkaEventWriter()
    sender=DataSender(writer)
    sender.send_event_transfer(freq,num)