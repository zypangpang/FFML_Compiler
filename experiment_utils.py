import random,functools
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


class EventHook:

    @classmethod
    def simple_transfer_hook(cls,cur_event,value):
        EventWriter.write_transfer({**cur_event,'value':value})



class TimeGenerator:
    def __init__(self,Y=2020,m=1,d=1,H=0,M=0,S=0):
        self.dt=datetime(Y,m,d,H,M,S)
        self.delta=timedelta(seconds=1)

    def set_delta(self,delta):
        self.delta=delta

    def get_next_time(self):
        r_str= self.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.dt=self.dt+self.delta
        return r_str

    def forward(self,time_unit,num=1):
        if time_unit=='d':
            self.dt=self.dt+timedelta(days=num)
        elif time_unit=='h':
            self.dt=self.dt+timedelta(hours=num)
        elif time_unit=='m':
            self.dt=self.dt+timedelta(minutes=num)


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
                            'eventtype':event
                        }
                        file.write(f"{id},{a_num},{channel},{time_str},{event}\n")
                        if event_hook: event_hook(cur_event)
                        id += 1
            dt.forward('h')

def simple_event_hook(cur_event):
    if cur_event['eventtype']=='transfer':
        EventHook.simple_transfer_hook(cur_event,500)



def test():
    dt=datetime.fromtimestamp(1577808000)
    print(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    d=timedelta(seconds=1)
    print(dt+d)

if __name__ == '__main__':

    channel="ONL"
    events=['failed_login','failed_login',"login",'transfer']
    #simple_data_generate(10,"exp_test.txt","ONL","transfer",500)
    events_file=FileManager.get_file('events')

    medium_data_generate(100,events_file,channel,[events,['login','password_change','transfer']],20,simple_event_hook)

    FileManager.close_all()


