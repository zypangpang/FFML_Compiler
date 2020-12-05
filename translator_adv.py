#import logging
import re
from typing import List

import constants
from constants import SYMBOL_TYPE, COUNTER_TYPE, PREDEFINED_EVENTS, TIME_UNIT
from parser import ASTNode
from utils import MyTemplate, bt, ListTemplate, log_info, log_collect
#from functools import reduce

"""
Symbol Attr Memo:
Policy: obj

"""

def set_opt_vars(level):
    global OPT_UNION_ALL, OPT_MERGE_TABLE, OPT_UDF, OPT_RETRACT
    OPT_UNION_ALL = True if level > 0 else False
    OPT_MERGE_TABLE = True if level >1  else False
    OPT_UDF = True if level >2 else False
    OPT_RETRACT = True if level >3 else False

    #OPT_UNION_ALL=False
    #OPT_UDF=False

def get_configs():
    global SEQ_TIME,SEQ_UNIT
    SEQ_TIME = constants.get_config_value('SEQ_TIME')
    SEQ_UNIT = constants.get_config_value('SEQ_UNIT')
    OPT_LEVEL= int(constants.get_config_value('OPT_LEVEL'))
    set_opt_vars(OPT_LEVEL)


class Symbol:
    def __init__(self, name: str, type: SYMBOL_TYPE, attr={}):
        self.name = name
        self.type = type
        self.attr = attr

    def addAttr(self, name, type):
        if name not in self.attr:
            self.attr[name] = Symbol(name, type)

    def __repr__(self):
        return f"<{self.name}:{self.type}>"

    def __str__(self):
        return f"<{self.name}:{self.type}:{self.attr}>"


class SymbolCounter:
    def __init__(self, init_value=0):
        self.__init_val = init_value
        self.__counters = {}

    def new_counter(self, name):
        if name in self.__counters:
            raise Exception("Counter already exists")
        self.__counters[name] = self.__init_val

    def get_counter(self, name):
        if name not in self.__counters:
            self.new_counter(name)
        return self.__counters[name]

    def inc_counter(self, name):
        if name not in self.__counters:
            log_collect(f"Define new counter <{name}>","info")
            self.__counters[name] = self.__init_val
        self.__counters[name] += 1
        return self.__counters[name]

    def add_counter(self, name, val):
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
            log_collect(f"Symbol {sym.name} redefined","info")
        self.symbols[sym.name] = sym

    def resolve(self, name):
        if name in self.symbols:
            return self.symbols[name]
        else:
            raise KeyError("Symbol not exist")

    def remove(self, name):
        if name in self.symbols:
            self.symbols.pop(name)

    def __str__(self):
        return f"GlobalScope: {self.symbols}"


class Policy:
    def __init__(self, name):
        self.name = name
        self.sql_statements = []

    def __iter__(self):
        self.i=0
        self.n=len(self.sql_statements)
        return self

    def __next__(self):
        if self.i>= self.n:
            raise StopIteration
        t=re.sub("\s+"," ",self.sql_statements[self.i])
        self.i+=1
        return t

    def add_sql(self, statement):
        self.sql_statements.append(statement)


    def __str__(self):
        ans = f"<!-- Policy name: {self.name} -->"
        for s in self.sql_statements:
            ans += f"\n{s}"
        ans+="\n<!-- Policy end -->"
        return ans


def get_template(name):
    t_map = {
        "SELECT": MyTemplate("SELECT $PROJ$ FROM $TABLE$ WHERE $CONDITION$"),
        "PROJ": MyTemplate("SELECT $PROJ$ FROM $TABLE$"),
        "CREATE_VIEW": MyTemplate("CREATE TEMPORARY VIEW $NAME$ AS ( $BODY$ )"), #if not GEN_JAVA else MyTemplate('createView("$NAME$","$BODY$");'),
        "UNION_ALL": ListTemplate("UNION ALL"),
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
        "SELECT_IN": MyTemplate("SELECT $PROJ$ FROM $TABLE$ WHERE $IN_COL$ IN ( $IN_BODY$ )"),
        "GROUPBY": MyTemplate("""SELECT $PROJ$ FROM $TABLE$ GROUP BY $KEY$"""),
        "WINDOW": MyTemplate("""SELECT $PROJ$ 
    FROM $TABLE$ 
    GROUP BY $KEY$,TUMBLE($TIME_KEY$, INTERVAL $INTERVAL$)"""),
        "WINDOW_WITH_END": MyTemplate("""SELECT $PROJ$, TUMBLE_END(rowtime, INTERVAL $INTERVAL$) AS rowtime 
FROM $TABLE$ 
GROUP BY $KEY$,TUMBLE(rowtime, INTERVAL $INTERVAL$)"""),
        "TOPN": MyTemplate("""SELECT $PROJ$ FROM
(
   SELECT *,
   ROW_NUMBER() OVER(PARTITION BY $KEY$ ORDER BY $ORDER$ DESC) as rownum
   FROM $TABLE$
)
WHERE rownum $CONDITION$ """),
        "JOIN": MyTemplate("""SELECT $PROJ$ 
FROM $LEFT$ $JOIN_TYPE$ $RIGHT$
ON $LEFT$.$KEY$ = $RIGHT$.$KEY$"""),
        "JOIN_WHERE": MyTemplate("""SELECT $PROJ$ 
FROM $LEFT$ $JOIN_TYPE$ $RIGHT$
ON $LEFT$.$KEY$ = $RIGHT$.$KEY$ WHERE $CONDITION$"""),
        "INSERT": MyTemplate("""INSERT INTO $TABLE$ $CONTENT$"""),
    }

    return t_map[name]


class ASTVisitor:
    def __init__(self):
        self.counters = SymbolCounter()
        self.policies = []

        self.table_kv={}
        self.tables=set()

        self.actions=set()

    def __reset_policy(self):
        self.symbol_table = SymbolTable()

    def __define_table(self, name, sql_temp):
        self.symbol_table.define(Symbol(name, SYMBOL_TYPE.TABLE, {'q': sql_temp.get_code()}))

    def __math_cal(self, a, op, b):
        d = {"+": a + b, "-": a - b, '*': a * b, '/': a / b}
        return d[op]

    def __update_current_table(self, table):
        self.symbol_table.define(Symbol("current_table", SYMBOL_TYPE.INTERNAL, {'value': table}))

    def create_view(self, sql_template, t_name, key, **kwargs):
        if t_name not in self.tables:
            template_view = get_template("CREATE_VIEW") \
                .set_value("NAME", bt(t_name)) \
                .set_value("BODY", sql_template.get_code())
            self.add_policy_sql(template_view)
            self.tables.add(t_name)
        self.symbol_table.define(Symbol(t_name, SYMBOL_TYPE.TABLE, {'q': sql_template.get_code(),'key':key, **kwargs}))
        return t_name

    def add_policy_sql(self, template):
        try:
            policy = self.symbol_table.resolve('policy').attr['obj']
        except KeyError:
            raise Exception("Policy object undefined")
        policy.add_sql(template.get_code())

    def __assemble_feature_str(self,*args):
        return  " ".join([arg.replace("`", "").replace(" ", "").lower() for arg in args])

    def action_check_repeat(self,*args):
        feature_str=self.__assemble_feature_str(*args)
        if feature_str in self.actions:
            return True
        else:
            self.actions.add(feature_str)
            return False

    def __opt_merge_table_get_new_name(self,type,*args):
        feature_str=self.__assemble_feature_str(*args)
        try:
            return self.table_kv[feature_str]
        except KeyError:
            name=self.__get_new_name(type)
            self.table_kv[feature_str]=name
            return name

    def get_new_name(self,type,*args):
        if OPT_MERGE_TABLE:
            return self.__opt_merge_table_get_new_name(type,*args)
        else:
            return self.__get_new_name(type)

    def __get_new_name(self, type):
        t_id = self.counters.inc_counter(type)
        return f"{type.name.lower()}_{t_id}"
        #other = None
        #if type == COUNTER_TYPE.PROCEDURE:
            #other = kwargs.get("func_name", None)
        #    other=args[0]
        #return f"{type.name.lower()}_{t_id}_{other}" if other else f"{type.name.lower()}_{t_id}"

    def __getfunc(self, name):
        def default_func(node):
            # log_print(f"visit {name}")
            for c in node.children:
                self.visit(c)

        func_name = f"visit_{name}"
        if hasattr(self, func_name):
            return getattr(self, func_name)
        else:
            return default_func

    def visit(self, node, **kwargs):
        return self.__getfunc(node.type)(node, **kwargs)

    def visit_PolicyList(self, node: ASTNode):
        get_configs()
        for ps in node.children:
            self.__reset_policy()
            policy = self.visit(ps)
            self.policies.append(policy)
        # log_print(f"Generated {len(node.children)} policies.")
        #print("****************")
        #print(self.table_kv)
        #print(self.tables)
        #print("****************")
        log_collect(f"Table numbers: {len(self.tables)}","info")
        return self.policies

    def visit_PolicyStatement(self, node: ASTNode):
        policy_name = self.visit(node.children[0])
        policy = Policy(policy_name)
        self.symbol_table.define(Symbol('policy', SYMBOL_TYPE.POLICY, {'obj': policy}))
        for cld in node.children[1:]:
            self.visit(cld)
        return policy

    def visit_String(self, node: ASTNode):
        # log_print("visit String " + node.value)
        return node.value

    def __opt_unionall_condition_tables(self,node:ASTNode):
        event_tables = self.symbol_table.resolve("event_table").attr['value']
        condition_tables=[]
        i=0
        while i < len(node.children):
            end=0
            for table in event_tables:
                j=i
                self.__update_current_table(table)
                cur_table=self.visit(node.children[j])
                self.__update_current_table(cur_table)
                j+=1
                while j < len(node.children) and self.visit(node.children[j])=="AND":
                    cur_table=self.visit(node.children[j+1])
                    self.__update_current_table(cur_table)
                    j+=2
                condition_tables.append(cur_table)
                end=j
            i=end+1
        return condition_tables

    def visit_ConditionStatement(self, node: ASTNode):
        if OPT_UNION_ALL:
            stack=self.__opt_unionall_condition_tables(node)
        else:
            stack = []
            event_table = self.symbol_table.resolve("event_table").attr['value'][0]
            self.__update_current_table(event_table)
            table = self.visit(node.children[0])
            stack.append(table)
            i = 1
            while i < len(node.children):
                op = self.visit(node.children[i])
                if op == "AND":
                    cur_table = stack.pop()
                    self.__update_current_table(cur_table)
                else:
                    event_table = self.symbol_table.resolve("event_table").attr['value'][0]
                    self.__update_current_table(event_table)
                stack.append(self.visit(node.children[i + 1]))
                i += 2

        if OPT_UNION_ALL:
            t_names=stack
        else:
            condition_sqls = [
                get_template("PROJ").set_value("PROJ", "*").set_value("TABLE", ctable) for ctable in stack
            ]
            template_union = get_template("UNION_ALL").set_list(condition_sqls)
            t_name=self.get_new_name(COUNTER_TYPE.CONDITION,"UNION_ALL","*",*stack)
            t_names = [self.create_view(template_union, t_name, key='id')]

        self.symbol_table.define(Symbol("condition_table", SYMBOL_TYPE.INTERNAL, {"type": "list", "value": t_names}))

    def visit_And(self, node):
        return "AND"

    def visit_Or(self, node):
        return "OR"

    def cast_rowtime(self,table,cols:list=()):

        cur_table_key = self.symbol_table.resolve(table).attr['key']
        cols_str=''
        if cols:
            try:
                cols.remove(cur_table_key)
            except:
                pass
            cols_str=",".join(cols)
        cast_table_t = get_template("PROJ")\
            .set_value("PROJ", f"{cur_table_key},{cols_str+',' if cols_str else ''} CAST(rowtime AS TIMESTAMP(3)) AS rowtime") \
            .set_value("TABLE", table)

        t_name = self.get_new_name(COUNTER_TYPE.CAST,"PROJ",*cast_table_t.get_key_value())

        self.create_view(cast_table_t, t_name, key=cur_table_key)
        return t_name

    def __cast_join(self,table,key,t_name,cur_table_key):
        cur_table_cast = self.cast_rowtime(table, [key])
        cond_table_cast = self.cast_rowtime(t_name)

        PROJ = f"{cur_table_cast}.*"
        TABLE = f"{cond_table_cast},{cur_table_cast}"
        CONDITION = f"{cond_table_cast}.{key}={cur_table_cast}.{key} AND {cur_table_cast}.rowtime >= {cond_table_cast}.rowtime"
        template = get_template("SELECT").set_value("PROJ", PROJ) \
            .set_value("TABLE", TABLE) \
            .set_value("CONDITION", CONDITION)  # BETWEEN {t_name}.rowtime AND {t_name}.rowtime + INTERVAL '1' DAY")

        t_name = self.get_new_name(COUNTER_TYPE.CONDITION, "SELECT", *template.get_key_value())
        self.create_view(template, t_name, key=cur_table_key)
        return t_name

    # @log_info
    def visit_SingleCondition(self, node: ASTNode):
        lhs: tuple = self.visit(node.children[0])
        comp = self.visit(node.children[1])
        rhs: tuple = self.visit(node.children[2])
        t_name, key = self.__cal_comp(lhs, comp, rhs)

        try:
            table = self.symbol_table.resolve("current_table").attr['value']
            cur_table_key=self.symbol_table.resolve(table).attr['key']
        except KeyError:
            raise Exception("Current table undefined or get key failed")

        if not OPT_UDF:
            t_name=self.__cast_join(table,key,t_name,cur_table_key)

        in_body_template=get_template("PROJ").set_value("PROJ", cur_table_key).set_value("TABLE", t_name)
        template = get_template("SELECT_IN").set_value("PROJ", "*").set_value("TABLE", table) \
           .set_value("IN_COL", cur_table_key).set_value("IN_BODY",in_body_template.get_code())
        t_name=self.get_new_name(COUNTER_TYPE.CONDITION,"SELECT_IN","*",table,cur_table_key,cur_table_key,t_name)
        self.create_view(template,t_name,key=cur_table_key)
        return t_name

    def visit_Condition(self, node):
        lhs: tuple = self.visit(node.children[0])
        comp = self.visit(node.children[1])
        rhs: tuple = self.visit(node.children[2])
        t_name, key = self.__cal_comp(lhs, comp, rhs)
        return t_name, key

    def visit_Comp(self, node: ASTNode):
        return node.value

    # @log_info
    def visit_EventStatement(self, node: ASTNode):
        events = []
        event_tables = []
        for c in node.children:
            last_event, event_table = self.visit(c)
            events.append(last_event)
            event_tables.append(event_table)
        for e in events:
            if e != events[0]:
                raise Exception("The last event of all event conditions need to be identical")
        self.symbol_table.define(Symbol("event", SYMBOL_TYPE.INTERNAL, {'type': 'str', 'value': events[0]}))

        if not OPT_UNION_ALL:
            event_sqls = [get_template("PROJ")
                              .set_value("PROJ", "*")
                              .set_value("TABLE", et)
                              .get_code() for et in event_tables]
            template_union = get_template("UNION_ALL").set_list(event_sqls)
            name=self.get_new_name(COUNTER_TYPE.EVENT,"UNION_ALL",'*',*sorted(event_tables))
            event_tables = [self.create_view(template_union, name, key='id')]

        self.symbol_table.define(Symbol("event_table", SYMBOL_TYPE.INTERNAL, {'type': 'list', 'value': event_tables}))
        #self.__update_current_table(event_tables)

    def visit_SingleEvent(self, node: ASTNode):
        # log_print("visit SingleEvent")
        children = node.children
        channel = self.visit(children[0])
        params = self.visit(children[1])
        if isinstance(params, str):
            ori_event_name = params
            # t_id=self.counters.inc_counter(COMMON_COUNTER['event'])
            # t_name=f"event_{t_id}"
            template_select = get_template("SELECT") \
                .set_value("PROJ", "*") \
                .set_value("TABLE", ori_event_name) \
                .set_value("CONDITION", f"channel='{channel}'")

            # template_view=get_template("CREATE_VIEW")\
            #    .set_value("NAME",bt(t_name))\
            #    .set_value("BODY",template_select.get_code())
            #
            #            sql=template_view.get_code()
            #            self.policy.add_sql(sql)
            #            self.symbol_table.define(Symbol(t_name,SYMBOL_TYPE.TABLE,{'q':template_select.get_code()}))
            t_name = self.get_new_name(COUNTER_TYPE.EVENT,"SELECT",*template_select.get_key_value())
            self.create_view(template_select, t_name, key='id')
            final_event_table = t_name
        else:
            # process seq time
            seq_time = params['time']
            if not seq_time.is_integer():
                log_collect(f"SEQ: {seq_time} is truncated to {int(seq_time)}",'warning')
            seq_time = int(seq_time)
            if SEQ_UNIT == TIME_UNIT.HOUR and seq_time >= 24 or seq_time >= 60:
                raise Exception(
                    f"Change SEQ time {seq_time} {SEQ_UNIT.name} to some {TIME_UNIT(SEQ_UNIT.value + 1).name}")

            event_seq = params['event_list']
            ori_event_name = event_seq[-1]

            if OPT_UNION_ALL:
                #t_name = f"{channel}_{ori_event_name}"
                tselect = get_template("SELECT") \
                    .set_value("PROJ", "*") \
                    .set_value("TABLE", bt(ori_event_name)) \
                    .set_value("CONDITION", f"channel = '{channel}'")
                ori_event_table=self.get_new_name(COUNTER_TYPE.EVENT,"SELECT",*tselect.get_key_value())
                self.create_view(tselect, ori_event_table, key='id')
                t_name="event"
            else:
                t_name,ori_event_table=self.__seq_event_union_all(event_seq,channel)


            #bt_event_seq = bt(event_seq)
            match_template = get_template("MATCH") \
                .set_value("PROJ", "*") \
                .set_value("TABLE", t_name) \
                .set_value("PARTITION", "accountnumber") \
                .set_value("ORDER", "rowtime") \
                .set_value("MEASURES", f"{event_seq[-1]}.id as id,{event_seq[-1]}.rowtime AS rowtime") \
                .set_value("PATTERN", " ".join(event_seq)) \
                .set_value("TIME_VAL", str(seq_time)) \
                .set_value("TIME_UNIT", SEQ_UNIT.name) \
                .set_value("DEFINE", ','.join([f"{item} AS eventtype='{item}'"
                                               for item in event_seq]))
            t_name = self.get_new_name(COUNTER_TYPE.EVENT,"MATCH",*match_template.get_key_value())
            self.create_view(match_template, t_name, key='id')

            in_template = get_template("SELECT_IN") \
                .set_value("PROJ", "*") \
                .set_value("TABLE", ori_event_table) \
                .set_value("IN_COL", "id") \
                .set_value("IN_BODY", get_template("PROJ").set_value("PROJ", "id")
                           .set_value("TABLE", t_name).get_code())
            t_name = self.get_new_name(COUNTER_TYPE.EVENT,"SELECT_IN","*",f"{channel}_{event_seq[-1]}","id","id","t_name")
            self.create_view(in_template, t_name, key='id')

            final_event_table = t_name

        # self.event_tables.append(final_event_table)
        return ori_event_name, final_event_table

    def __seq_event_union_all(self,event_seq,channel):
        union_list = []
        union_names=[]
        for event in event_seq:
            tselect = get_template("SELECT") \
                .set_value("PROJ", "*") \
                .set_value("TABLE", bt(event)) \
                .set_value("CONDITION", f"channel = '{channel}'")
            t_name = self.get_new_name(COUNTER_TYPE.EVENT,*tselect.get_key_value() )
            self.create_view(tselect, t_name, key='id')
            union_names.append(t_name)
            union_list.append(get_template("PROJ")
                              .set_value("PROJ", f"id,accountnumber,rowtime,eventtype")
                              .set_value("TABLE", bt(t_name))
                              .get_code())

        union_smt = get_template("UNION_ALL").set_list(union_list)
        # t_id = self.counters.inc_counter(COMMON_COUNTER['event'])
        # t_name = f"event_{t_id}"
        t_name = self.get_new_name(COUNTER_TYPE.EVENT,"UNION_ALL",f"id,accountnumber,rowtime,eventtype",*sorted(union_names))
        self.create_view(union_smt, t_name, key='id')
        return t_name,union_names[-1]

    def visit_Channel(self, node: ASTNode):
        # log_print("visit Channel")
        return node.value

    def visit_Event(self, node: ASTNode):
        # log_print("visit Event")
        ori_event_name = node.value['str']
        if ori_event_name not in PREDEFINED_EVENTS:
            raise Exception("Event not supported")
        try:
            self.symbol_table.define(Symbol(ori_event_name, SYMBOL_TYPE.EVENT, {'key': "id"}))
        except Exception as e:
            pass
        return ori_event_name
        # t_id=self.counters.get_counter(COMMON_COUNTER['event'])
        # t_name=f"event_{t_id}"
        # sql=f"CREATE VIEW {t_name} AS SELECT * FROM {ori_event_name} WHERE channel = '{channel}'"
        # self.policy.add_sql(sql)
        # return t_name

    def visit_EventParam(self, node):
        event = node.value[0]['str']  # format: {name:'<ID>', str: 'xxx'}
        param = node.value[1]['str']
        try:
            legal_event = self.symbol_table.resolve("event").attr['value']
        except KeyError:
            raise Exception("No event statement defined")
        if event != legal_event:
            raise Exception(f"Only parameters of last event '{legal_event}' can be used")
        return (event, param)

    def visit_Sequence(self, node):
        # log_print("visit Sequence")
        res_data = {
            "time": None,
            "event_list": None
        }
        if len(node.children) == 1:
            log_collect(f"No SEQ time specified. Use default {SEQ_TIME} {SEQ_UNIT}",'warning')
            res_data['time'] = SEQ_TIME
            res_data['event_list'] = self.visit(node.children[0])
        else:
            res_data['time'] = self.visit(node.children[0])
            res_data['event_list'] = self.visit(node.children[1])
        return res_data

    def visit_Digits(self, node):
        # log_print("visit Digits")
        return node.value

    def visit_Boolean(self, node):
        return "TRUE" if node.value else "FALSE"

    def visit_Name(self, node):
        return node.value

    def visit_Query(self, node):
        return self.visit_Procedure(node)

    def visit_Procedure(self, node):
        func_name = self.visit(node.children[0])['str']
        params = self.visit(node.children[1])
        return BuiltInFuncs.call_func(func_name, params, self)

    def visit_Int(self, node):
        return int(node.value)

    def visit_HistStatement(self, node: ASTNode):
        hist_days = self.visit(node.children[0])
        try:
            self.symbol_table.resolve("hist_days").attr['value'] = hist_days
        except KeyError:
            self.symbol_table.define(Symbol("hist_days", SYMBOL_TYPE.INTERNAL, {'type': 'int', 'value': hist_days}))

        cond_table, key = self.visit(node.children[1])
        self.symbol_table.resolve("hist_days").attr['value'] = 1

        if OPT_UDF:
            if OPT_RETRACT:
                template = get_template("WINDOW").set_value("PROJ", f"{key},MAX(rowtime) AS rowtime,COUNT(*) AS daycount") \
                    .set_value("TABLE", cond_table) \
                    .set_value("KEY", key) \
                    .set_value("TIME_KEY","rowtime") \
                    .set_value("INTERVAL", f"'1' SECOND")
                #template = get_template("GROUPBY").set_value("PROJ", f"{key}, COUNT(*) AS daycount") \
                #    .set_value("TABLE", cond_table).set_value("KEY", key)
            else:
                template = get_template("GROUPBY").set_value("PROJ", f"{key},rowtime,COUNT(*) AS daycount") \
                    .set_value("TABLE", cond_table).set_value("KEY", key)
        else:
            template = get_template("GROUPBY").set_value("PROJ", f"{key}, COUNT(*) AS daycount, MAX(rowtime) AS rowtime") \
                .set_value("TABLE", cond_table).set_value("KEY", key)
        t_name = self.get_new_name(COUNTER_TYPE.COUNT,"GROUPBY",*template.get_key_value())
        self.create_view(template, t_name, key=key)
        return t_name, "daycount"

    # def visit_Condition(self,node:ASTNode,daycount):
    #    pass

    def __get_key_and_idop(self, lhs, rhs):
        left_key = self.symbol_table.resolve(lhs[0]).attr['key']
        right_key = self.symbol_table.resolve(rhs[0]).attr['key']

        key = 'id' if left_key == 'id' or right_key == 'id' else 'accountnumber'
        id_op = lhs if left_key == 'id' else rhs  # the operand with the 'key'

        join_key = 'accountnumber'
        if left_key == 'id' and right_key == 'id':
            join_key = 'id'
        return key, id_op, join_key

    def __cal_comp(self, lhs, comp, rhs):
        if isinstance(lhs, tuple) and isinstance(rhs, tuple):
            key, id_op, join_key = self.__get_key_and_idop(lhs, rhs)
            if id_op != rhs:
                raise Exception("id operator must be rhs")
            template=get_template("SELECT").set_value("PROJ",f"{id_op[0]}.{key} AS {key}, {id_op[0]}.rowtime AS rowtime ") \
                                .set_value("TABLE",f"{lhs[0]}, {rhs[0]}") \
                                .set_value("CONDITION",
                                           f"{lhs[0]}.{join_key}={rhs[0]}.{join_key} AND {rhs[0]}.rowtime "
                                           f">= {lhs[0]}.rowtime AND "
                                           f"{lhs[0]}.`{lhs[1]}` {comp} {rhs[0]}.`{rhs[1]}`")
                                           #f"BETWEEN {lhs[0]}.rowtime AND {lhs[0]}.rowtime + INTERVAL '1' DAY ")
            #template = get_template("JOIN_WHERE").set_value("PROJ", f"{id_op[0]}.{key} AS {key}") \
            #    .set_value("LEFT", lhs[0]).set_value("RIGHT", rhs[0]) \
            #    .set_value("KEY", join_key).set_value("CONDITION", f"{lhs[0]}.`{lhs[1]}` {comp} {rhs[0]}.`{rhs[1]}`") \
            #    .set_value("JOIN_TYPE", "INNER JOIN")
            t_name = self.get_new_name(COUNTER_TYPE.COMPARISON,"SELECT",*template.get_key_value())
            self.create_view(template, t_name, key=key)
        elif isinstance(lhs, tuple):
            key = self.symbol_table.resolve(lhs[0]).attr['key']
            template = get_template("SELECT").set_value("PROJ", key+", rowtime").set_value("TABLE", lhs[0]) \
                .set_value("CONDITION", f"`{lhs[1]}` {comp} {rhs}")
            t_name = self.get_new_name(COUNTER_TYPE.COMPARISON,"SELECT",*template.get_key_value())
            self.create_view(template, t_name, key=key)
        else:
            raise Exception("The left side of comparison must be Query or expression with parameters.")
        return t_name, key

    def __cal_op(self, left, op, right):
        # print(left, op, right)
        if isinstance(left, float) and isinstance(right, float):
            return self.__math_cal(left, op, right)
        if isinstance(left, tuple) and isinstance(right, tuple):
            # id_operator = left if self.symbol_table.resolve(left[0]).attr['key'] == 'id' else right
            key, id_op, join_key = self.__get_key_and_idop(left, right)
            template = get_template("JOIN").set_value("PROJ",
                                                      f"{id_op[0]}.{key} AS {key}, {left[0]}.`{left[1]}`"
                                                      f" {op} {right[0]}.`{right[1]}` AS `result`") \
                .set_value("LEFT", left[0]).set_value("RIGHT", right[0]) \
                .set_value("KEY", join_key) \
                .set_value("JOIN_TYPE", "INNER JOIN")
            t_name = self.get_new_name(COUNTER_TYPE.MATH,"JOIN",*template.get_key_value())
            self.create_view(template, t_name, key=key)
            return t_name, 'result'
        if isinstance(right, tuple):
            t = left
            left = right
            right = t

        if isinstance(left, tuple):
            key = self.symbol_table.resolve(left[0]).attr['key']
            template = get_template("PROJ").set_value("PROJ", f"{key},`{left[1]}` {op} {right} AS `result`") \
                .set_value("TABLE", left[0])
            t_name = self.get_new_name(COUNTER_TYPE.MATH,"PROJ",*template.get_key_value())
            self.create_view(template, t_name, key=key)
            return t_name, 'result'

    def __cal_expression(self, node):
        result_stack = []
        result_stack.append(self.visit(node.children[0]))
        i = 1
        while i < len(node.children):
            op = self.visit(node.children[i])
            rhs = self.visit(node.children[i + 1])
            res = self.__cal_op(result_stack.pop(), op, rhs)
            # print(res)
            result_stack.append(res)
            i += 2
        return result_stack.pop()

    def visit_Factor(self, node):
        return self.__cal_expression(node)

        '''
        if len(node.children) == 1:
            return self.visit(node.children[0])
        if node.children[0].type=="Query":
            query_t_name,query_value_name=self.visit(node.children[0])
            print(self.visit(node.children[1]))
            print(self.visit(node.children[2]))
        else:
            # simple mathematical computation.
            pass
        '''

    def visit_Expression(self, node):
        return self.__cal_expression(node)

    def visit_AddOp(self, node):
        return node.value

    def visit_MultiOp(self, node):
        return node.value

    def visit_ChannelList(self, node):
        return [self.visit(c) for c in node.children]

    def visit_Params(self, node):
        return [{'type': c.type, 'value': self.visit(c)} for c in node.children]

    def visit_EventSeq(self, node):
        # log_print("visit EventSeq")
        event_list = []
        for c in node.children:
            event_list.append(self.visit(c))
        return event_list


class BuiltInFuncs:
    funcs = {
        'totaldebit': {
            "param_type": [('Channel', 'Digits', 'Int'), ('ChannelList', 'Digits', 'Int'), ],
        },
        'badaccount': {
            "param_type": [('EventParam',)],
        },
        'alert': {
            "param_type": [('EventParam', 'EventParam')],
        },
        'block': {
            "param_type": [('EventParam', 'EventParam')],
        },
    }

    @classmethod
    def verify_params(cls, func_name, params):
        param_types = cls.funcs[func_name]['param_type']
        ok = False
        given_params = tuple(c['type'] for c in params)
        for _params in param_types:
            if given_params == _params:
                ok = True
                break
        return ok

    @classmethod
    def build_params(cls, func_name, params, visitor):
        return getattr(cls, f"params_{func_name}")(params, visitor)

    # Param check and build function for each builtin function
    @classmethod
    def params_totaldebit(cls, params, visitor):
        try:
            daycount = visitor.symbol_table.resolve("hist_days").attr['value']
        except KeyError:
            daycount = 1
        if len(params) == 1:
            params.append({'type': 'Digits', 'value': 1.0})
        if len(params) == 2:
            params.append({'type': 'Int', 'value': daycount})
        if not cls.verify_params("totaldebit", params):
            raise Exception("TOTALDEBIT requires 1 or 2 parameters: Channel|ChannelList, [interval]")
        return params

    @classmethod
    def params_badaccount(cls, params, visitor):
        print(params)
        if not cls.verify_params("badaccount", params):
            raise Exception("BADACCOUNT requires 1 parameter: Event.accountnumber")
        return params

    @classmethod
    def params_alert(cls, params, visitor):
        if not cls.verify_params("alert", params):
            raise Exception("ALERT requires 2 parameters: Event.id, Event.accountnumber")
        return params

    @classmethod
    def params_block(cls, params, visitor):
        if not cls.verify_params("block", params):
            raise Exception("BLOCK requires 2 parameters: Event.id, Event.accountnumber")
        return params

    # Procedure for each builtin function
    @classmethod
    def __insert_table(cls, t_name, params, visitor:ASTVisitor):
        try:
            cond_tables = visitor.symbol_table.resolve("condition_table").attr['value']
        except KeyError:
            raise Exception("Condition table not defined")
        proj = ','.join([bt(param['value'][1]) for param in params])
        for cond_table in cond_tables:
            template = get_template("INSERT").set_value("TABLE", t_name) \
                .set_value("CONTENT", get_template("PROJ")
                           .set_value("PROJ", proj)
                           .set_value("TABLE", cond_table).get_code())
            if not visitor.action_check_repeat(t_name,proj,cond_table):
                visitor.add_policy_sql(template)

    @classmethod
    def alert(cls, params, visitor):
        cls.__insert_table('alert', params, visitor)

    @classmethod
    def block(cls, params, visitor):
        cls.__insert_table('block', params, visitor)

    @classmethod
    def totaldebit(cls, params, visitor: ASTVisitor):
        if OPT_UDF:
            return cls.__totaldebit_udf(params,visitor)
        else:
            return cls.__totaldebit_stream(params,visitor)

    @classmethod
    def __totaldebit_udf(cls, params, visitor: ASTVisitor):
        try:
            cur_table = visitor.symbol_table.resolve("current_table").attr['value']
        except KeyError:
            raise Exception("Current table not defined")

        if not params[1]['value'].is_integer():
            log_collect(f"TOTALDEBIT: {params[1]['value']} is truncated to {int(params[1]['value'])}", 'warning')
            # logging.warning(f"TOTALDEBIT: {params[1]['value']} is truncated to {int(params[1]['value'])}")

        channels = [params[0]['value']] if params[0]['type'] == "Channel" else params[0]['value']
        interval = int(params[1]['value'])
        daycount = int(params[2]['value'])

        template = get_template("PROJ").set_value("PROJ", "S.id,S.rowtime,T.v as totaldebit") \
            .set_value("TABLE", f"{cur_table} as S, LATERAL TABLE(TOTALDEBIT(accountnumber,"
                                f"'{','.join(channels)}',{interval},{daycount})) as T(v)")

        # template = get_template("PROJ").set_value("PROJ", f"*,TOTALDEBIT(accountnumber,{'_'.join(channels)}, {interval}) AS totaldebit") \
        #    .set_value("TABLE", cur_table)#.set_value("KEY", "accountnumber")
        new_table = visitor.create_view(template, visitor.get_new_name(COUNTER_TYPE.PROCEDURE,*template.get_key_value()),
                                        key="id")
        return new_table, "totaldebit"

    @classmethod
    def __totaldebit_stream(cls, params, visitor: ASTVisitor):
        channels=[params[0]['value']] if params[0]['type'] == "Channel" else params[0]['value']
        #table_name = '_'.join(channels) + "_transfer"
        #try:
        #    visitor.symbol_table.resolve(table_name)
        #except KeyError:
        condition_str = " OR ".join([f"channel='{c}'" for c in channels])
        t = get_template("SELECT").set_value("PROJ", "*").set_value("TABLE", "transfer") \
            .set_value("CONDITION", condition_str)
        table_name=visitor.get_new_name(COUNTER_TYPE.EVENT,"SELECT",*t.get_key_value())
        visitor.create_view(t, table_name, key='id')

        if not params[1]['value'].is_integer():
            log_collect(f"TOTALDEBIT: {params[1]['value']} is truncated to {int(params[1]['value'])}",'warning')
        interval = int(params[1]['value'])
        daycount = int(params[2]['value'])
        template = get_template("WINDOW_WITH_END").set_value("PROJ", "accountnumber, SUM(`value`) AS totaldebit") \
            .set_value("TABLE", table_name) \
            .set_value("KEY", "accountnumber") \
            .set_value("INTERVAL", f"'{interval}' DAY")
        t_name = visitor.get_new_name(COUNTER_TYPE.PROCEDURE, "WINDOW_WITH_END",*template.get_key_value())
        visitor.create_view(template, t_name, key='accountnumber')
        #template=get_template("SELECT").set_value("PROJ", "accountnumber, totaldebit, rowtime")\
        #                .set_value("TABLE",t_name)\
        #                .set_value("CONDITION",f"rowtime >= CURRENT_TIMESTAMP - INTERVAL '{daycount}' DAY")
        template = get_template("TOPN").set_value("PROJ", "accountnumber, totaldebit, rowtime") \
            .set_value("KEY", "accountnumber") \
            .set_value("ORDER", "rowtime") \
            .set_value("TABLE", t_name) \
            .set_value("CONDITION", f'<= {daycount}')
        t_name = visitor.get_new_name(COUNTER_TYPE.PROCEDURE, *template.get_key_value())
        visitor.create_view(template, t_name, key='accountnumber')
        return t_name, 'totaldebit'

    @classmethod
    def badaccount(cls, params, visitor: ASTVisitor):
        try:
            cur_table = visitor.symbol_table.resolve("current_table").attr['value']
        except KeyError:
            raise Exception("Current table not defined")
        template = get_template("GROUPBY").set_value("PROJ", "accountnumber,BADACCOUNT(accountnumber) AS isbad") \
            .set_value("TABLE", cur_table).set_value("KEY", "accountnumber")
        new_table = visitor.create_view(template, visitor.get_new_name(COUNTER_TYPE.PROCEDURE, *template.get_key_value()),
                                        key="accountnumber")
        return new_table, "isbad"

    # Main call entry
    @classmethod
    def call_func(cls, name, params, visitor):
        name = name.lower()
        if name not in cls.funcs:
            raise KeyError(f"Function {name.upper()} not found")
        params = cls.build_params(name, params, visitor)
        return getattr(cls, name)(params, visitor)


if __name__ == '__main__':
    def abc(a, b, c):
        print(a, b, c)


    def test1(**kwargs):
        abc(**kwargs)


    test1(a=1, b=2, c=3)
