import abc,json

from kafka import KafkaProducer


class FileManager:
    #events_path = "/home/zypang/IdeaProjects/blink-test/spend-report/data/event.csv"
    pathes={
        "events":"./data/exp_events.csv",
        'transfer':"./data/exp_transfer.csv",
        'result':'./data/exp_result.csv',
    }
    heads={
        "events":"id,accountnumber,channel,rowtime,eventtype",
        "transfer":"id, accountnumber, sortcode, value, channel, rowtime, eventtype",
        "result":"id",
    }
    file_objs={}
    #transfer_path="/home/zypang/IdeaProjects/blink-test/spend-report/data/transfer.csv"

    @classmethod
    def get_file(cls,name):
        if name not in cls.pathes:
            raise KeyError("Unknown file name")

        if name not in cls.file_objs:
            cls.file_objs[name]=open(cls.pathes[name],'w')
            cls.file_objs[name].write(cls.heads[name]+'\n')

        return cls.file_objs[name]

    @classmethod
    def get_path(cls,name):
        return cls.pathes[name]


    @classmethod
    def close_all(cls):
        for name in cls.file_objs:
            cls.file_objs[name].close()
        cls.file_objs={}

class EventWriter(abc.ABC):
    @abc.abstractmethod
    def write_transfer(self,event_dict):
        pass
    @abc.abstractmethod
    def write_event(self,event_dict):
        pass

    @abc.abstractmethod
    def write_result_id(self,event_dict):
        pass

class FileEventWriter(EventWriter):
    def write_transfer(self,event_dict):
        file=FileManager.get_file('transfer')
        sortcode=1
        file.write(f"{event_dict['id']},{event_dict['accountnumber']},{sortcode},{event_dict['value']},"
                   f"{event_dict['channel']},{event_dict['rowtime']},{event_dict['eventtype']}\n")
    def write_event(self,event_dict):
        file=FileManager.get_file('events')
        file.write(f"{event_dict['id']},{event_dict['accountnumber']},{event_dict['channel']},{event_dict['rowtime']},{event_dict['eventtype']}\n")

    def write_result_id(self,event_dict):
        file=FileManager.get_file('result')
        file.write(str(event_dict['id']))

class KafkaEventWriter(EventWriter):
    def __init__(self):
        self.producer = KafkaProducer(bootstrap_servers="localhost:9092",value_serializer=lambda v: json.dumps(v).encode('utf-8'))

    def write_transfer(self,event_dict):
        self.producer.send("transfer",event_dict)

    def write_event(self,event_dict):
        self.producer.send("event",event_dict)

    def write_result_id(self,event_dict):
        self.producer.send("correct_result",event_dict)
