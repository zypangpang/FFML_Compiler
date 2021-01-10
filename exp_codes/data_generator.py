import random,functools
from collections import defaultdict
from datetime import datetime,timedelta
import time
from common import FileEventWriter, FileManager


#class KafkaHelper():
#    producer = KafkaProducer(bootstrap_servers="localhost:9092",value_serializer=lambda v: json.dumps(v).encode('utf-8'))
#
#    @classmethod
#    def send_data(cls,topic,dict_value):
#        cls.producer.send(topic,dict_value)


class TransferAggregator:
    def __init__(self):
        #self.cur_time_obj=None
        self.transcount=defaultdict(lambda: defaultdict(int))
        self.totaldebit=defaultdict(lambda: defaultdict(int))

    def aggregate(self,cur_event):
        date_str=str(datetime.strptime(cur_event['rowtime'],TimeGenerator.TIME_FORMAT).date())
        a_num=cur_event['accountnumber']
        value=cur_event['value']
        self.transcount[a_num][date_str]+=1
        self.totaldebit[a_num][date_str]+=value

    def output(self):
        print("Transcount:")
        for k,v in self.transcount.items():
            print(f"{k}: {dict(v)}")
        print("Totaldebit:")
        for k,v in self.totaldebit.items():
            print(f"{k}: {dict(v)}")

class TransferResultCollector:

    def __init__(self,event_writer,aggregator,policy):
        self.aggregator=aggregator
        self.policy=policy
        self.event_writer=event_writer

    def collect_result(self,cur_event):
        if self.policy=='Simple':
            if cur_event['value']>=500:
                self.event_writer.write_result_id(cur_event)

        elif self.policy=='Medium':
            pass
        elif self.policy=='Complex1':
            pass
        elif self.policy=='Complex2':
            pass
        else:
            raise Exception("Unknown policy")


class TimeGenerator:
    TIME_FORMAT ="%Y-%m-%dT%H:%M:%SZ"

    def __init__(self,Y=2020,m=1,d=1,H=0,M=0,S=0):
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

def simple_data_generate(event_writer,num, channel,event,event_hook=None,):
    range_end = num // 10
    dt = TimeGenerator()
    for id in range(num):
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
        event_writer.write_event(cur_event)
        if event_hook: event_hook(cur_event)
        # dt.forward('h',random.randint(1,2))
        # dt.forward('h',1)



def medium_data_generate(event_writer,num,channel,events_list,duration,event_hook=None):
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
                        if event_hook: event_hook(cur_event)
                        id += 1
            dt.forward('h')

class MediumEventHook:
    def __init__(self,event_writer,aggregator=None,tmin=100,tmax=500):
        #self.bit=True
        self.event_writer=event_writer
        self.transfer_value_min=tmin
        self.transfer_value_max=tmax
        self.aggregator=aggregator

    def hook(self,cur_event):
        if cur_event['eventtype']=='transfer':
            cur_event['value']=random.randint(self.transfer_value_min,self.transfer_value_max)
            self.event_writer.write_transfer(cur_event)
            #EventHook.simple_transfer_hook(cur_event,)
            if self.aggregator:
                self.aggregator.aggregate(cur_event)




def simple_generate():
    channel="ONL"
    #events_file=FileManager.get_file("events")
    event_writer=FileEventWriter()
    m_hook=MediumEventHook(event_writer,tmin=400,tmax=700)
    simple_data_generate(event_writer,1000,channel,"transfer",m_hook.hook)


def medium_generate():
    channel="ONL"
    events=['failed_login','failed_login',"login",'transfer']
    #simple_data_generate(10,"exp_test.txt","ONL","transfer",500)
    events_file=FileManager.get_file('events')

    event_writer=FileEventWriter()
    aggregator=TransferAggregator()
    m_hook=MediumEventHook(event_writer=event_writer,aggregator=aggregator)
    medium_data_generate(event_writer,100,channel,[events],300,m_hook.hook)
    m_hook.aggregator.output()


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
        simple_generate()
    except Exception as e:
        print(e)
    FileManager.close_all()
