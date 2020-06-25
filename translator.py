from constants import SYMBOL_TYPE,COUNTER_TYPE, SEQ_TIME,SEQ_UNIT,PREDEFINED_EVENTS,LOG_LEVEL,TIME_UNIT
from parser import ASTNode
from utils import log_print,MyTemplate,bt,ListTemplate
"""
Symbol Attr Memo:
Policy: obj

"""
class Symbol:
    def __init__(self, name: str, type: SYMBOL_TYPE,attr={}):
        self.name = name
        self.type = type
        self.attr = attr

    def addAttr(self, name, type):
        if name not in self.attr:
            self.attr[name] = Symbol(name, type)

    def __repr__(self):
        return f"<{self.name}:{self.type}>"

    def __str__(self):
        return f"<{self.name}:{self.type}>"

class SymbolCounter:
    def __init__(self,init_value=0):
        self.__init_val=init_value
        self.__counters={}

    def new_counter(self,name):
        if name in self.__counters:
            raise Exception("Counter already exists")
        self.__counters[name] = self.__init_val

    def get_counter(self,name):
        if name not in self.__counters:
            self.new_counter(name)
        return self.__counters[name]

    def inc_counter(self,name):
        if name not in self.__counters:
            log_print(f"Define new counter <{name}>")
            self.__counters[name] = self.__init_val
        self.__counters[name]+=1
        return self.__counters[name]

    def add_counter(self,name,val):
        if name not in self.__counters:
            raise Exception("No such counter")
        self.__counters[name] += val
        return self.__counters[name]

    def __str__(self):
        return f"All counters: {self.__counters}"



'''
class EventSymbol(Symbol):
    def __init__(self, name, type):
        Symbol.__init__(self, name, type)
        self.attributes = {}

    def addAttr(self, name, type):
        if name not in self.attributes:
            self.attributes[name] = Symbol(name, type)

    def __repr__(self):
        return f"<{self.name}:{self.type}:{self.attributes}>"

    def __str__(self):
        return f"<{self.name}:{self.type}:{self.attributes}>"


class ChannelSymbol(Symbol):
    pass

class TableSymbol:
    pass
'''

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def define(self, sym: Symbol):
        if sym.name in self.symbols:
            raise Exception(f"Policy {sym.name} redefined")
        self.symbols[sym.name] = sym

    def resolve(self, name):
        if name in self.symbols:
            return self.symbols[name]
        else:
            return None

    def __str__(self):
        return f"GlobalScope: {self.symbols}"


class Policy:
    def __init__(self,name):
        self.name=name
        self.sql_statements=[]

    def add_sql(self,statement):
        self.sql_statements.append(statement)

    def __str__(self):
        ans=f"<{self.name}>:"
        for s in self.sql_statements:
            ans+=f"\n> {s}"
        return ans

def get_template(name):
    t_map={
        "SELECT":MyTemplate("SELECT $PROJ$ FROM $TABLE$ WHERE $CONDITION$"),
        "PROJ":MyTemplate("SELECT $PROJ$ FROM $TABLE$"),
        "CREATE_VIEW":MyTemplate("CREATE VIEW $NAME$ AS ( $BODY$ )"),
        "UNION_ALL":ListTemplate("UNION ALL"),
        "MATCH": MyTemplate(
            """SELECT $PROJ$ FROM $TABLE$
MATCH_RECOGNIZE (
    PARTITION BY $PARTITION$
    ORDER BY $ORDER$
    MEASURES $MEASURES$
    ONE ROW PER MATCH
    AFTER MATCH SKIP PAST LAST ROW
    PATTERN ($PATTERN$) WITHIN INTERVAL '$TIME_VAL$' $TIME_UNIT$
    DEFINE
       $DEFINE$
)"""),
       "SELECT_IN":MyTemplate("SELECT $PROJ$ FROM $TABLE$ WHERE $IN_COL$ IN ( $IN_BODY$ )"),
    }
    return t_map[name]


class ASTVisitor:
    def __init__(self):
        self.counters = SymbolCounter()
        self.policies={}
        self.symbol_table=SymbolTable()

    def __reset_policy(self):
        self.events=[]
        self.policy=Policy(None)

    def __create_view(self,name,body):
        return get_template("CREATE_VIEW") \
            .set_value("NAME", bt(name)) \
            .set_value("BODY", body)

    def __get_new_name(self,type):
        t_id=self.counters.inc_counter(type)
        return f"{type.name.lower()}_{t_id}"

    def __getfunc(self,name):
        def default_func(node):
            log_print(f"visit {name}")
            for c in node.children:
                self.visit(c)

        func_name=f"visit_{name}"
        if hasattr(self,func_name):
            return getattr(self,func_name)
        else:
            return default_func

    def visit(self, node,**kwargs):
        return self.__getfunc(node.type)(node,**kwargs)

    def visit_PolicyList(self, node: ASTNode):
        for ps in node.children:
            self.__reset_policy()
            self.visit(ps)
        log_print(f"Generated {len(node.children)} policies.")

    def visit_PolicyStatement(self, node: ASTNode):
        self.policy.name=self.visit(node.children[0])
        self.symbol_table.define(Symbol(self.policy.name,SYMBOL_TYPE.POLICY,{'obj':self.policy}))
        for cld in node.children[1:]:
            self.visit(cld)

    def visit_String(self, node: ASTNode):
        log_print("visit String "+node.value)
        return node.value

    def visit_ConditionStatement(self,node:ASTNode):
        log_print("visit ConditionStatement")


    def visit_Actions(self,node:ASTNode):
        log_print("visit Actions")

    def visit_SingleEvent(self,node:ASTNode):
        log_print("visit SingleEvent")
        children=node.children
        channel=self.visit(children[0])
        params=self.visit(children[1])
        if isinstance(params,str):
            ori_event_name=params
            #t_id=self.counters.inc_counter(COMMON_COUNTER['event'])
            #t_name=f"event_{t_id}"
            t_name=self.__get_new_name(COUNTER_TYPE.EVENT)
            template_select=get_template("SELECT")\
                .set_value("PROJ","*")\
                .set_value("TABLE",bt(ori_event_name))\
                .set_value("CONDITION",f"channel='{channel}'")
            template_view=get_template("CREATE_VIEW")\
                .set_value("NAME",bt(t_name))\
                .set_value("BODY",template_select.get_code())
            sql=template_view.get_code()
            self.policy.add_sql(sql)
            self.symbol_table.define(Symbol(t_name,SYMBOL_TYPE.TABLE,{'q':template_select.get_code()}))
            final_event_table=t_name
        else:
            # process seq time
            seq_time=params['time']
            if not seq_time.is_integer():
                log_print(f"{seq_time} is truncated to {int(seq_time)}",LOG_LEVEL.WARNING)
                seq_time=int(seq_time)
            if SEQ_UNIT==TIME_UNIT.HOUR and seq_time>=24 or seq_time>=60:
                raise Exception(f"Change SEQ time {seq_time} {SEQ_UNIT.name} to some {TIME_UNIT(SEQ_UNIT.value+1).name}")

            event_seq=params['event_list']
            union_list=[]
            for event in event_seq:
                t_name=f"{channel}_{event}"
                tselect=get_template("SELECT")\
                    .set_value("PROJ","*")\
                    .set_value("TABLE",bt(event))\
                    .set_value("CONDITION",f"channel = '{channel}'")
                template_view = self.__create_view(t_name,tselect.get_code())
                self.symbol_table.define(Symbol(t_name,SYMBOL_TYPE.TABLE,{'q':tselect.get_code()}))
                self.policy.add_sql(template_view.get_code())

                union_list.append(get_template("PROJ")
                                     .set_value("PROJ","accountnumber,rowtime,eventtype")
                                     .set_value("TABLE",bt(t_name))
                                     .get_code())

            union_smt=get_template("UNION_ALL").set_list(union_list)
            #t_id = self.counters.inc_counter(COMMON_COUNTER['event'])
            #t_name = f"event_{t_id}"
            t_name=self.__get_new_name(COUNTER_TYPE.EVENT)
            tview_sql=self.__create_view(t_name,union_smt.get_code()).get_code()
            self.policy.add_sql(tview_sql)
            self.symbol_table.define(Symbol(t_name,SYMBOL_TYPE.TABLE,{'q':union_smt.get_code()}))

            bt_event_seq=bt(event_seq)
            match_template=get_template("MATCH")\
                                .set_value("PROJ","*")\
                                .set_value("TABLE",t_name)\
                                .set_value("PARTITION","accountnumber")\
                                .set_value("ORDER","rowtime")\
                                .set_value("MEASURES",f"{event_seq[-1]}.rowtime AS rowtime")\
                                .set_value("PATTERN"," ".join(event_seq))\
                                .set_value("TIME_VAL",str(seq_time))\
                                .set_value("TIME_UNIT",SEQ_UNIT.name)\
                                .set_value("DEFINE",','.join([f"{item} AS {item}.eventtype='{item}'"
                                                              for item in event_seq]))
            t_name=self.__get_new_name(COUNTER_TYPE.EVENT)
            tview_sql=self.__create_view(t_name,match_template.get_code()).get_code()
            self.policy.add_sql(tview_sql)
            #self.symbol_table.define(Symbol(t_name,SYMBOL_TYPE.TABLE,{'q':match_template.get_code()}))
            self.__define_table(t_name,match_template)

            in_template=get_template("SELECT_IN")\
                            .set_value("PROJ","*")\
                            .set_value("TABLE",f"{channel}_{event_seq[-1]}")\
                            .set_value("IN_COL","accountnumber")\
                            .set_value("IN_BODY",get_template("PROJ").set_value("PROJ","accountnumber")
                                                                    .set_value("TABLE",t_name).get_code())
            t_name=self.__get_new_name(COUNTER_TYPE.EVENT)
            tview_sql=self.__create_view(t_name,in_template.get_code()).get_code()
            self.policy.add_sql(tview_sql)
            self.__define_table(t_name,in_template)

            final_event_table=t_name
        self.events.append(final_event_table)

    def __define_table(self,name,sql_temp):
        self.symbol_table.define(Symbol(name, SYMBOL_TYPE.TABLE, {'q': sql_temp.get_code()}))

    def visit_Channel(self,node:ASTNode):
        log_print("visit Channel")
        return node.value

    def visit_Event(self,node:ASTNode):
        log_print("visit Event")
        ori_event_name=node.value['str']
        if ori_event_name not in PREDEFINED_EVENTS:
            raise Exception("Event not supported")
        try:
            self.symbol_table.define(Symbol(ori_event_name,SYMBOL_TYPE.EVENT))
        except Exception as e:
            pass
        return ori_event_name
        #t_id=self.counters.get_counter(COMMON_COUNTER['event'])
        #t_name=f"event_{t_id}"
        #sql=f"CREATE VIEW {t_name} AS SELECT * FROM {ori_event_name} WHERE channel = '{channel}'"
        #self.policy.add_sql(sql)
        #return t_name

    def visit_Sequence(self,node):
        log_print("visit Sequence")
        res_data={
            "time":None,
            "event_list":None
        }
        if len(node.children)==1:
            log_print(f"No SEQ time specified. Use default {SEQ_TIME} {SEQ_UNIT}",LOG_LEVEL.WARNING)
            res_data['time']=SEQ_TIME
            res_data['event_list'] = self.visit(node.children[0])
        else:
            res_data['time']=self.visit(node.children[0])
            res_data['event_list']=self.visit(node.children[1])
        return res_data

    def visit_Digits(self,node):
        log_print("visit Digits")
        return node.value

    def visit_EventSeq(self,node):
        log_print("visit EventSeq")
        event_list=[]
        for c in node.children:
            event_list.append(self.visit(c))
        return event_list


if __name__ == '__main__':
    def abc(a,b,c):
        print(a,b,c)

    def test1(**kwargs):
        abc(**kwargs)
    test1(a=1,b=2,c=3)

