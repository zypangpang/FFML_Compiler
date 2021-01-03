import random,functools
from collections import defaultdict
from datetime import datetime,timedelta

class FileManager:
    events_path = "exp_events.csv"
    transfer_path = 'exp_transfer.csv'
    events_file=None
    transfer_file=None

    @classmethod
    def get_file(cls,name):
        if name=='transfer':
            if cls.transfer_file is None:
                cls.transfer_file = open(cls.transfer_path, 'w')
                head = "id, accountnumber, sortcode, value, channel, rowtime, eventtype"
                cls.transfer_file.write(head+'\n')

            return cls.transfer_file
        if name=='events':
            if cls.events_file is None:
                cls.events_file = open(cls.events_path, 'w')
                head = "id,accountnumber,channel,rowtime,eventtype"
                cls.events_file.write(head+'\n')

            return cls.events_file

    @classmethod
    def close_all(cls):
        if cls.transfer_file:
            cls.transfer_file.close()
        if cls.events_file:
            cls.events_file.close()

class EventWriter:
    @classmethod
    def write_transfer(cls,event_dict,file=None):
        if not file:
            file=FileManager.get_file('transfer')
        sortcode=1
        file.write(f"{event_dict['id']},{event_dict['a_num']},{sortcode},{event_dict['value']},"
                   f"{event_dict['channel']},{event_dict['time']},{event_dict['eventtype']}\n")


class TransferAggregator:
    def __init__(self):
        #self.cur_time_obj=None
        self.transcount=defaultdict(lambda: defaultdict(int))
        self.totaldebit=defaultdict(lambda: defaultdict(int))

    def aggregate(self,cur_event):
        date_str=str(datetime.strptime(cur_event['time'],TimeGenerator.TIME_FORMAT).date())
        a_num=cur_event['a_num']
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




class EventHook:

    @classmethod
    def simple_transfer_hook(cls,cur_event,value):
        EventWriter.write_transfer({**cur_event,'value':value})


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

def simple_data_generate(num,file,channel,event,event_hook=None):
    range_end = num // 10
    dt = TimeGenerator()
    for id in range(num):
        account_number = random.randint(0, range_end)
        time_str = dt.get_next_time()
        cur_event = {
            'id': id,
            'a_num': account_number,
            'channel': channel,
            'time': time_str,
            'eventtype': event,
            # 'next_time_obj': dt
        }
        file.write(f"{id},{account_number},{channel},{time_str},{event}\n")
        if event_hook: event_hook(cur_event)
        #dt.forward('h',random.randint(1,2))
        dt.forward('h',1)


def medium_data_generate(num,file,channel,events_list,duration,event_hook=None):
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
                            'a_num':a_num,
                            'channel':channel,
                            'time':time_str,
                            'eventtype':event,
                            #'next_time_obj': dt
                        }
                        file.write(f"{id},{a_num},{channel},{time_str},{event}\n")
                        if event_hook: event_hook(cur_event)
                        id += 1
            dt.forward('h')

class MediumEventHook:
    def __init__(self,tmin=100,tmax=500):
        #self.bit=True
        self.transfer_value_min=tmin
        self.transfer_value_max=tmax
        self.aggregator=TransferAggregator()

    def hook(self,cur_event):
        if cur_event['eventtype']=='transfer':
            cur_event['value']=random.randint(self.transfer_value_min,self.transfer_value_max)
            EventWriter.write_transfer(cur_event)
            #EventHook.simple_transfer_hook(cur_event,)
            self.aggregator.aggregate(cur_event)



def test():
    dt=datetime.fromtimestamp(1577808000)
    print(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    d=timedelta(seconds=1)
    print(dt+d)
    print(dt.date())
    exit(0)

if __name__ == '__main__':
    #test()

    channel="ONL"
    events=['failed_login','failed_login',"login",'transfer']
    #simple_data_generate(10,"exp_test.txt","ONL","transfer",500)
    events_file=FileManager.get_file('events')

    m_hook=MediumEventHook()
    #medium_data_generate(100,events_file,channel,[["transfer"]],300,m_hook.hook)
    simple_data_generate(100,events_file,channel,"transfer",m_hook.hook)
    m_hook.aggregator.output()

    FileManager.close_all()


