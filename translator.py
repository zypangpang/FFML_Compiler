import logging
import re

from constants import SYMBOL_TYPE, COUNTER_TYPE, SEQ_TIME, SEQ_UNIT, PREDEFINED_EVENTS, LOG_LEVEL, TIME_UNIT,GEN_JAVA
from parser import ASTNode
from utils import MyTemplate, bt, ListTemplate, log_info
from functools import reduce

"""
Symbol Attr Memo:
Policy: obj

"""


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
            logging.info(f"Define new counter <{name}>")
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
            logging.info(f"Symbol {sym.name} redefined")
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
        "WINDOW": MyTemplate("""SELECT $PROJ$,TUMBLE_END(rowtime, INTERVAL $INTERVAL$) AS rowtime 
FROM $TABLE$ 
GROUP BY $KEY$,TUMBLE(rowtime, INTERVAL $INTERVAL$)"""),
        "TOPN": MyTemplate("""SELECT $PROJ$ FROM
(
   SELECT $PROJ$,
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

    def __reset_policy(self):
        self.symbol_table = SymbolTable()

    def __define_table(self, name, sql_temp):
        self.symbol_table.define(Symbol(name, SYMBOL_TYPE.TABLE, {'q': sql_temp.get_code()}))

    def __math_cal(self, a, op, b):
        d = {"+": a + b, "-": a - b, '*': a * b, '/': a / b}
        return d[op]

    def __update_current_table(self, table):
        self.symbol_table.define(Symbol("current_table", SYMBOL_TYPE.INTERNAL, {'value': table}))

    def create_view(self, sql_template, t_name, **kwargs):
        template_view = get_template("CREATE_VIEW") \
            .set_value("NAME", bt(t_name)) \
            .set_value("BODY", sql_template.get_code())
        self.add_policy_sql(template_view)
        self.symbol_table.define(Symbol(t_name, SYMBOL_TYPE.TABLE, {'q': sql_template.get_code(), **kwargs}))
        return t_name

    def add_policy_sql(self, template):
        try:
            policy = self.symbol_table.resolve('policy').attr['obj']
        except KeyError:
            raise Exception("Policy object undefined")
        policy.add_sql(template.get_code())

    def get_new_name(self, type, **kwargs):
        t_id = self.counters.inc_counter(type)
        other = None
        if type == COUNTER_TYPE.PROCEDURE:
            other = kwargs.get("func_name", None)
        return f"{type.name.lower()}_{t_id}_{other}" if other else f"{type.name.lower()}_{t_id}"

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
        for ps in node.children:
            self.__reset_policy()
            policy = self.visit(ps)
            self.policies.append(policy)
        # log_print(f"Generated {len(node.children)} policies.")
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

    def visit_ConditionStatement(self, node: ASTNode):
        stack = []
        table = self.visit(node.children[0])
        stack.append(table)
        i = 1
        while i < len(node.children):
            op = self.visit(node.children[i])
            cur_table = stack.pop()
            if op == "AND":
                self.__update_current_table(cur_table)
            else:
                event_table = self.symbol_table.resolve("event_table").attr['value']
                self.__update_current_table(event_table)
            stack.append(self.visit(node.children[i + 1]))
            i += 2
        t_name = stack.pop()
        self.symbol_table.define(Symbol("condition_table", SYMBOL_TYPE.INTERNAL, {"type": "str", "value": t_name}))

    def visit_And(self, node):
        return "AND"

    def visit_Or(self, node):
        return "OR"

    # @log_info
    def visit_SingleCondition(self, node: ASTNode):
        lhs: tuple = self.visit(node.children[0])
        comp = self.visit(node.children[1])
        rhs: tuple = self.visit(node.children[2])
        t_name, key = self.__cal_comp(lhs, comp, rhs)

        try:
            table = self.symbol_table.resolve("current_table").attr['value']
        except KeyError:
            raise Exception("Current table undefined")

        template= get_template("SELECT").set_value("PROJ",f"{table}.*") \
                        .set_value("TABLE",f"{t_name},{table}") \
                        .set_value("CONDITION",f"{t_name}.{key}={table}.{key} AND "
                                               f"{table}.rowtime >= {t_name}.rowtime") #BETWEEN {t_name}.rowtime AND {t_name}.rowtime + INTERVAL '1' DAY")
        #template = get_template("SELECT_IN").set_value("PROJ", "*").set_value("TABLE", table) \
        #    .set_value("IN_COL", key).set_value("IN_BODY", get_template("PROJ")
        #                                        .set_value("PROJ", key)
        #                                        .set_value("TABLE", t_name).get_code())

        t_name = self.get_new_name(COUNTER_TYPE.CONDITION)
        self.create_view(template, t_name, key='transid')
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
        event_sqls = [get_template("PROJ")
                          .set_value("PROJ", "*")
                          .set_value("TABLE", et)
                          .get_code() for et in event_tables]
        template_union = get_template("UNION_ALL").set_list(event_sqls)
        event_table = self.create_view(template_union, self.get_new_name(COUNTER_TYPE.EVENT), key='transid')
        self.symbol_table.define(Symbol("event_table", SYMBOL_TYPE.INTERNAL, {'type': 'str', 'value': event_table}))
        self.__update_current_table(event_table)

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
                .set_value("TABLE", bt(ori_event_name)) \
                .set_value("CONDITION", f"channel='{channel}'")

            # template_view=get_template("CREATE_VIEW")\
            #    .set_value("NAME",bt(t_name))\
            #    .set_value("BODY",template_select.get_code())
            #
            #            sql=template_view.get_code()
            #            self.policy.add_sql(sql)
            #            self.symbol_table.define(Symbol(t_name,SYMBOL_TYPE.TABLE,{'q':template_select.get_code()}))
            t_name = self.get_new_name(COUNTER_TYPE.EVENT)
            self.create_view(template_select, t_name, key='transid')
            final_event_table = t_name
        else:
            # process seq time
            seq_time = params['time']
            if not seq_time.is_integer():
                logging.warning(f"SEQ: {seq_time} is truncated to {int(seq_time)}")
                seq_time = int(seq_time)
            if SEQ_UNIT == TIME_UNIT.HOUR and seq_time >= 24 or seq_time >= 60:
                raise Exception(
                    f"Change SEQ time {seq_time} {SEQ_UNIT.name} to some {TIME_UNIT(SEQ_UNIT.value + 1).name}")

            event_seq = params['event_list']
            ori_event_name = event_seq[-1]
            union_list = []
            for event in event_seq:
                t_name = f"{channel}_{event}"
                tselect = get_template("SELECT") \
                    .set_value("PROJ", "*") \
                    .set_value("TABLE", bt(event)) \
                    .set_value("CONDITION", f"channel = '{channel}'")
                self.create_view(tselect, t_name, key='transid')
                union_list.append(get_template("PROJ")
                                  .set_value("PROJ", f"accountnumber,rowtime,'{event}' AS eventtype")
                                  .set_value("TABLE", bt(t_name))
                                  .get_code())

            union_smt = get_template("UNION_ALL").set_list(union_list)
            # t_id = self.counters.inc_counter(COMMON_COUNTER['event'])
            # t_name = f"event_{t_id}"
            t_name = self.get_new_name(COUNTER_TYPE.EVENT)
            self.create_view(union_smt, t_name, key='transid')

            bt_event_seq = bt(event_seq)
            match_template = get_template("MATCH") \
                .set_value("PROJ", "*") \
                .set_value("TABLE", t_name) \
                .set_value("PARTITION", "accountnumber") \
                .set_value("ORDER", "rowtime") \
                .set_value("MEASURES", f"{event_seq[-1]}.rowtime AS rowtime") \
                .set_value("PATTERN", " ".join(event_seq)) \
                .set_value("TIME_VAL", str(seq_time)) \
                .set_value("TIME_UNIT", SEQ_UNIT.name) \
                .set_value("DEFINE", ','.join([f"{item} AS {item}.eventtype='{item}'"
                                               for item in event_seq]))
            t_name = self.get_new_name(COUNTER_TYPE.EVENT)
            self.create_view(match_template, t_name, key='accountnumber')

            in_template = get_template("SELECT_IN") \
                .set_value("PROJ", "*") \
                .set_value("TABLE", f"{channel}_{event_seq[-1]}") \
                .set_value("IN_COL", "accountnumber") \
                .set_value("IN_BODY", get_template("PROJ").set_value("PROJ", "accountnumber")
                           .set_value("TABLE", t_name).get_code())
            t_name = self.get_new_name(COUNTER_TYPE.EVENT)
            self.create_view(in_template, t_name, key='transid')

            final_event_table = t_name

        # self.event_tables.append(final_event_table)
        return ori_event_name, final_event_table

    def visit_Channel(self, node: ASTNode):
        # log_print("visit Channel")
        return node.value

    def visit_Event(self, node: ASTNode):
        # log_print("visit Event")
        ori_event_name = node.value['str']
        if ori_event_name not in PREDEFINED_EVENTS:
            raise Exception("Event not supported")
        try:
            self.symbol_table.define(Symbol(ori_event_name, SYMBOL_TYPE.EVENT, {'key': "transid"}))
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
            logging.warning(f"No SEQ time specified. Use default {SEQ_TIME} {SEQ_UNIT}")
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

        template = get_template("GROUPBY").set_value("PROJ", f"{key}, COUNT(*) AS daycount, MAX(rowtime) AS rowtime") \
            .set_value("TABLE", cond_table).set_value("KEY", key)
        t_name = self.get_new_name(COUNTER_TYPE.COUNT)
        self.create_view(template, t_name, key=key)
        return t_name, "daycount"

    # def visit_Condition(self,node:ASTNode,daycount):
    #    pass

    def __get_key_and_idop(self, lhs, rhs):
        left_key = self.symbol_table.resolve(lhs[0]).attr['key']
        right_key = self.symbol_table.resolve(rhs[0]).attr['key']

        key = 'transid' if left_key == 'transid' or right_key == 'transid' else 'accountnumber'
        id_op = lhs if left_key == 'transid' else rhs  # the operand with the 'key'

        join_key = 'accountnumber'
        if left_key == 'transid' and right_key == 'transid':
            join_key = 'transid'
        return key, id_op, join_key

    def __cal_comp(self, lhs, comp, rhs):
        if isinstance(lhs, tuple) and isinstance(rhs, tuple):
            key, id_op, join_key = self.__get_key_and_idop(lhs, rhs)
            if id_op != rhs:
                lhs,rhs=rhs,lhs
            template=get_template("SELECT").set_value("PROJ",f"{id_op[0]}.{key} AS {key}, {id_op[0]}.rowtime AS rowtime ") \
                                .set_value("TABLE",f"{lhs[0]}, {rhs[0]}") \
                                .set_value("CONDITION",
                                           f"{lhs[0]}.{join_key}={rhs[0]}.{join_key} AND {rhs[0]}.rowtime "
                                           f">= {lhs[0]}.rowtime")
                                           #f"BETWEEN {lhs[0]}.rowtime AND {lhs[0]}.rowtime + INTERVAL '1' DAY ")
            #template = get_template("JOIN_WHERE").set_value("PROJ", f"{id_op[0]}.{key} AS {key}") \
            #    .set_value("LEFT", lhs[0]).set_value("RIGHT", rhs[0]) \
            #    .set_value("KEY", join_key).set_value("CONDITION", f"{lhs[0]}.`{lhs[1]}` {comp} {rhs[0]}.`{rhs[1]}`") \
            #    .set_value("JOIN_TYPE", "INNER JOIN")
            t_name = self.get_new_name(COUNTER_TYPE.COMPARISON)
            self.create_view(template, t_name, key=key)
        elif isinstance(lhs, tuple):
            key = self.symbol_table.resolve(lhs[0]).attr['key']
            template = get_template("SELECT").set_value("PROJ", key+", rowtime").set_value("TABLE", lhs[0]) \
                .set_value("CONDITION", f"`{lhs[1]}` {comp} {rhs}")
            t_name = self.get_new_name(COUNTER_TYPE.COMPARISON)
            self.create_view(template, t_name, key=key)
        else:
            raise Exception("The left side of comparison must be Query or expression with parameters.")
        return t_name, key

    def __cal_op(self, left, op, right):
        # print(left, op, right)
        if isinstance(left, float) and isinstance(right, float):
            return self.__math_cal(left, op, right)
        if isinstance(left, tuple) and isinstance(right, tuple):
            # id_operator = left if self.symbol_table.resolve(left[0]).attr['key'] == 'transid' else right
            key, id_op, join_key = self.__get_key_and_idop(left, right)
            template = get_template("JOIN").set_value("PROJ",
                                                      f"{id_op[0]}.{key} AS {key}, {left[0]}.`{left[1]}`"
                                                      f" {op} {right[0]}.`{right[1]}` AS `result`") \
                .set_value("LEFT", left[0]).set_value("RIGHT", right[0]) \
                .set_value("KEY", join_key) \
                .set_value("JOIN_TYPE", "INNER JOIN")
            t_name = self.get_new_name(COUNTER_TYPE.MATH)
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
            t_name = self.get_new_name(COUNTER_TYPE.MATH)
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
            raise Exception("ALERT requires 2 parameters: Event.transid, Event.accountnumber")
        return params

    @classmethod
    def params_block(cls, params, visitor):
        if not cls.verify_params("block", params):
            raise Exception("BLOCK requires 2 parameters: Event.transid, Event.accountnumber")
        return params

    # Procedure for each builtin function
    @classmethod
    def __insert_table(cls, t_name, params, visitor):
        try:
            cond_table = visitor.symbol_table.resolve("condition_table").attr['value']
        except KeyError:
            raise Exception("Condition table not defined")
        proj = ','.join([bt(param['value'][1]) for param in params])
        template = get_template("INSERT").set_value("TABLE", t_name) \
            .set_value("CONTENT", get_template("PROJ")
                       .set_value("PROJ", proj)
                       .set_value("TABLE", cond_table).get_code())
        visitor.add_policy_sql(template)

    @classmethod
    def alert(cls, params, visitor):
        cls.__insert_table('alert', params, visitor)

    @classmethod
    def block(cls, params, visitor):
        cls.__insert_table('block', params, visitor)

    @classmethod
    def totaldebit_try(cls, params, visitor: ASTVisitor):
        channels = [params[0]['value']] if params[0]['type'] == "Channel" else params[0]['value']
        table_name = '_'.join(channels) + "_transfer"
        try:
            visitor.symbol_table.resolve(table_name)
        except KeyError:
            condition_str = " OR ".join([f"channel='{c}'" for c in channels])
            t = get_template("SELECT").set_value("PROJ", "*").set_value("TABLE", "transfer") \
                .set_value("CONDITION", condition_str)
            visitor.create_view(t, table_name, key='transid')

        if not params[1]['value'].is_integer():
            logging.warning(f"TOTALDEBIT: {params[1]['value']} is truncated to {int(params[1]['value'])}")
        interval = int(params[1]['value'])
        daycount = int(params[2]['value'])
        t_name = visitor.get_new_name(COUNTER_TYPE.PROCEDURE, func_name='totaldebit')

        template = get_template("GROUPBY").set_value("PROJ", f"accountnumber,TOTALDEBIT(accountnumber,{interval}) AS totaldebit") \
            .set_value("TABLE", table_name).set_value("KEY", "accountnumber")
        new_table = visitor.create_view(template, visitor.get_new_name(COUNTER_TYPE.PROCEDURE, func_name='totaldebit'),
                                        key="accountnumber")
        return new_table, "totaldebit"

    @classmethod
    def totaldebit(cls, params, visitor: ASTVisitor):
        channels=[params[0]['value']] if params[0]['type'] == "Channel" else params[0]['value']
        table_name = '_'.join(channels) + "_transfer"
        try:
            visitor.symbol_table.resolve(table_name)
        except KeyError:
            condition_str = " OR ".join([f"channel='{c}'" for c in channels])
            t = get_template("SELECT").set_value("PROJ", "*").set_value("TABLE", "transfer") \
                .set_value("CONDITION", condition_str)
            visitor.create_view(t, table_name, key='transid')

        if not params[1]['value'].is_integer():
            logging.warning(f"TOTALDEBIT: {params[1]['value']} is truncated to {int(params[1]['value'])}")
        interval = int(params[1]['value'])
        daycount = int(params[2]['value'])
        t_name = visitor.get_new_name(COUNTER_TYPE.PROCEDURE, func_name='totaldebit')
        template = get_template("WINDOW").set_value("PROJ", "accountnumber, SUM(`value`) AS totaldebit") \
            .set_value("TABLE", table_name) \
            .set_value("KEY", "accountnumber") \
            .set_value("INTERVAL", f"'{interval}' DAY")
        visitor.create_view(template, t_name, key='accountnumber')
        #template=get_template("SELECT").set_value("PROJ", "accountnumber, totaldebit, rowtime")\
        #                .set_value("TABLE",t_name)\
        #                .set_value("CONDITION",f"rowtime >= CURRENT_TIMESTAMP - INTERVAL '{daycount}' DAY")
        template = get_template("TOPN").set_value("PROJ", "accountnumber, totaldebit, rowtime") \
            .set_value("KEY", "accountnumber") \
            .set_value("ORDER", "rowtime") \
            .set_value("TABLE", t_name) \
            .set_value("CONDITION", f'<= {daycount}')
        t_name = visitor.get_new_name(COUNTER_TYPE.PROCEDURE, func_name='totaldebit')
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
        new_table = visitor.create_view(template, visitor.get_new_name(COUNTER_TYPE.PROCEDURE, func_name='badaccount'),
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
