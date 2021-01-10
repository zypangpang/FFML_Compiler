from common import FileManager,KafkaEventWriter
import time,csv

class DataSender:

    def __init__(self,event_writer):
        self.event_writer=event_writer

    def send_event_transfer(self,freq):
        sleep_sec=1/freq

        event_file=open(FileManager.get_path('events'),'r')
        transfer_file=open(FileManager.get_path('transfer'),'r')
        event_reader=csv.DictReader(event_file)
        transfer_reader=csv.DictReader(transfer_file)

        try:
            while True:
                time.sleep(sleep_sec)
                cur_event=event_reader.__next__()
                print(cur_event)
                #cur_event['id']=int(cur_event['id'])
                #cur_event['accountnumber']=int(cur_event['accountnumberid'])
                self.event_writer.write_event(cur_event)
                if cur_event['eventtype']=='transfer':
                    transfer_event=transfer_reader.__next__()
                    print(transfer_event)
                    #transfer_event['id']=int(transfer_event['id'])
                    #transfer_event['accountnumber']=int(transfer_event['accountnumber'])
                    #transfer_event['value']=float(transfer_event['value'])
                    self.event_writer.write_transfer(transfer_event)
        except Exception as e:
            print(e)

        event_file.close()
        transfer_file.close()

if __name__ == '__main__':
    writer=KafkaEventWriter()
    sender=DataSender(writer)
    sender.send_event_transfer(1)