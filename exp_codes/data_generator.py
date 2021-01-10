import random,functools
from collections import defaultdict
from datetime import datetime,timedelta,date
import time
from common import FileEventWriter, FileManager


#class KafkaHelper():
#    producer = KafkaProducer(bootstrap_servers="localhost:9092",value_serializer=lambda v: json.dumps(v).encode('utf-8'))
#
#    @classmethod
#    def send_data(cls,topic,dict_value):
#        cls.producer.send(topic,dict_value)

random.seed(0)

class TransferValueAssigner:
    def __init__(self,event_writer,tmin=100,tmax=800):
        #self.bit=True
        self.event_writer=event_writer
        self.transfer_value_min=tmin
        self.transfer_value_max=tmax
        #self.aggregator=aggregator

    def hook(self,cur_event):
        if cur_event['eventtype']=='transfer':
            self.assign_value(cur_event)
            #EventHook.simple_transfer_hook(cur_event,)
            #if self.aggregator:
            #    self.aggregator.aggregate(cur_event)

    def assign_value(self,cur_event):
        cur_event['value'] = random.randint(self.transfer_value_min, self.transfer_value_max)
        self.event_writer.write_transfer(cur_event)

class TransferAggregator:
    def __init__(self):
        #self.cur_time_obj=None
        self.transcount={
            "ONL":defaultdict(list),
            "ATM":defaultdict(list),
            "CNP":defaultdict(list),
        }
        self.totaldebit={
            "ONL":defaultdict(list),
            "ATM":defaultdict(list),
            "CNP":defaultdict(list),
        }
        self.cur_date=date(1989,1,1)

    def hook(self,cur_event):
        if cur_event['eventtype'] == 'transfer':
            self.aggregate(cur_event)

    def aggregate(self,cur_event):
        a_num=cur_event['accountnumber']
        value=cur_event['value']
        channel=cur_event['channel']
        row_date=datetime.strptime(cur_event['rowtime'],TimeGenerator.TIME_FORMAT).date()
        if row_date<self.cur_date:
            self.cur_date=row_date
            self.transcount[channel][a_num].append([str(row_date),0])
            self.totaldebit[channel][a_num].append([str(row_date),0])
        elif row_date> self.cur_date:
            print("Error: late event")
            return

        if not self.transcount[channel][a_num]:
            self.transcount[channel][a_num].append([str(row_date), 0])
            self.totaldebit[channel][a_num].append([str(row_date), 0])
        self.transcount[channel][a_num][-1][1]+=1
        self.totaldebit[channel][a_num][-1][1]+=value

    def get_latest_totaldebit(self,channel,accountnumber,num):
        return self.totaldebit[channel][accountnumber][-num:][1]

    def get_latest_transcount(self,channel,accountnumber,num):
        return self.transcount[channel][accountnumber][-num:][1]


    def output(self):
        print("Transcount:")
        for k,v in self.transcount.items():
            print(k)
            for k, v in v.items():
                print(f"{k}: {dict(v)}")
        print("Totaldebit:")
        for k,v in self.totaldebit.items():
            print(k)
            for k, v in v.items():
                print(f"{k}: {dict(v)}")

class TransferResultCollector:

    def __init__(self,event_writer,aggregator:TransferAggregator,policy):
        self.aggregator=aggregator
        self.policy=policy
        self.event_writer=event_writer

    def hook(self,cur_event):
        if cur_event['eventtype'] == 'transfer':
            self.collect_result(cur_event)

    def collect_result(self,cur_event):
        if self.policy=='Simple':
            if cur_event['value']>=500:
                self.event_writer.write_result_id(cur_event)

        elif self.policy=='Medium':
            totaldebit=self.aggregator.get_latest_totaldebit("ONL",cur_event['accountnumber'],1)[0]
            if totaldebit>=500 and cur_event['value']>=1500:
                self.event_writer.write_result_id(cur_event)

        elif self.policy=='Complex1':
            a_num=cur_event['accountnumber']
            totaldebit=self.aggregator.get_latest_totaldebit("ONL",a_num,1)[0]
            history_tt=self.aggregator.get_latest_totaldebit("ONL",a_num,5)
            history_num=functools.reduce(lambda cur_num,tt:cur_num+1 if tt>=250 else cur_num,history_tt,0)
            if totaldebit+cur_event['value']>=250 and history_num>=3:
                self.event_writer.write_result_id(cur_event)

        elif self.policy=='Complex2':
            a_num=cur_event['accountnumber']
            ONL_totaldebit=sum(self.aggregator.get_latest_totaldebit("ONL",a_num,3))
            CNP_totaldebit=sum(self.aggregator.get_latest_totaldebit("CNP",a_num,3))
            ONL_transcount = sum(self.aggregator.get_latest_transcount("ONL", a_num, 3))
            CNP_transcount = sum(self.aggregator.get_latest_transcount("CNP", a_num, 3))
            if cur_event['value']>=250 and ONL_totaldebit+CNP_totaldebit>2000 and ONL_transcount+CNP_transcount>20:
                self.event_writer.write_result_id(cur_event)
        else:
            raise Exception("Unknown policy")



class TimeGenerator:
    TIME_FORMAT ="%Y-%m-%dT%H:%M:%SZ"

    def __init__(self,Y=1900,m=1,d=1,H=0,M=0,S=0):
        self.dt=datetime(Y,m,d,H,M,S)
        self.delta=timedelta(seconds=1)

    def set_delta(self,delta):
        self.delta=delta

    def get_next_time(self):
        r_str= self.dt.strftime(self.TIME_FORMAT)
        self.dt=self.dt+self.delta
        return r_str

    def forward(self,time_unit,num=1):
        if time_unit=='d':
            self.dt=self.dt+timedelta(days=num)
        elif time_unit=='h':
            self.dt=self.dt+timedelta(hours=num)
        elif time_unit=='m':
            self.dt=self.dt+timedelta(minutes=num)


'''
def simple_data_generate(num, file, channel, event, value):
    #with open(path,'w') as file:
        #head= "id, accountnumber, sortcode, value, channel, rowtime, eventtype"
        #file.write(head+'\n')
        range_end=num//10
        sortcode=1
        hit=0
        dt=TimeGenerator()
        for id in range(num):
            account_number=random.randint(0,range_end)
            if hit: v=random.randrange(value,value*2)
            else: v=random.randrange(1,value)
            hit^=1
            time_str=dt.get_next_time()
            file.write(f"{id},{account_number},{sortcode},{v},{channel},{time_str},{event}\n")
'''

def continuous_data_generate(event_writer,num,sleep_sec, channel,event,event_hook=None,):
    range_end = num // 10
    dt = TimeGenerator()
    id=0
    while True:
        time.sleep(sleep_sec)
        account_number = random.randint(0, range_end)
        time_str = dt.get_next_time()
        cur_event = {
            'id': id,
            'accountnumber': account_number,
            'channel': channel,
            'rowtime': time_str,
            'eventtype': event,
            # 'next_time_obj': dt
        }
        # file.write(f"{id},{account_number},{channel},{time_str},{event}\n")
        event_writer.write_event(cur_event)
        if event_hook: event_hook(cur_event)
        # dt.forward('h',random.randint(1,2))
        # dt.forward('h',1)
        id+=1

def simple_data_generate(event_writer,num, channels,event,event_hook=[],):
    range_end = num // 10
    dt = TimeGenerator()
    id=0
    while id < num:
        for channel in channels:
            account_number = random.randint(0, range_end)
            time_str = dt.get_next_time()
            cur_event = {
                'id': id,
                'accountnumber': account_number,
                'channel': channel,
                'rowtime': time_str,
                'eventtype': event,
                # 'next_time_obj': dt
            }
            id+=1
            event_writer.write_event(cur_event)
            if event_hook:
                for hook in event_hook:
                    hook(cur_event)
        # dt.forward('h',random.randint(1,2))
        # dt.forward('h',1)



def medium_data_generate(event_writer,num,channel,events_list,duration,event_hook=[]):
    #with open(path,'w') as file:
        #head="id,accountnumber,channel,rowtime,eventtype"
        #file.write(head+'\n')
        dt=TimeGenerator()
        id=0
        event_num=functools.reduce(lambda a,b: a+len(b),events_list,0)
        row_per_event=duration//(event_num+1)
        while id<num:
            for events in events_list:
                for event in events:
                    for a_num in range(row_per_event):
                        time_str=dt.get_next_time()
                        cur_event={
                            'id':id,
                            'accountnumber':a_num,
                            'channel':channel,
                            'rowtime':time_str,
                            'eventtype':event,
                            #'next_time_obj': dt
                        }
                        event_writer.write_event(cur_event)
                        #file.write(f"{id},{a_num},{channel},{time_str},{event}\n")
                        if event_hook:
                            for hook in event_hook:
                                hook(cur_event)
                        id += 1
            dt.forward('h')





def simple_generate():
    channel="ONL"
    #events_file=FileManager.get_file("events")
    event_writer=FileEventWriter()
    m_hook=TransferValueAssigner(event_writer, tmin=400, tmax=800)
    simple_data_generate(event_writer,1000,channel,"transfer",[m_hook.hook])


def medium_generate():
    channel="ONL"
    events=['failed_login','failed_login',"login",'transfer']
    #simple_data_generate(10,"exp_test.txt","ONL","transfer",500)

    event_writer=FileEventWriter()
    assigner=TransferValueAssigner(event_writer=event_writer)
    aggregator=TransferAggregator()
    result_collector=TransferResultCollector(event_writer,aggregator,'Simple')
    medium_data_generate(event_writer,100,channel,[events],300,[assigner.hook,aggregator.hook,result_collector.hook])
    aggregator.output()


def test():
    #dt=datetime.fromtimestamp(1577808000)
    dt=datetime.utcnow()
    print(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    d=timedelta(seconds=1)
    print(dt+d)
    print(dt.date())
    exit(0)


if __name__ == '__main__':
    try:
        medium_generate()
    except Exception as e:
        print(e)
        raise e
    FileManager.close_all()
