from constants import SYMBOL_TYPE, COUNTER_TYPE, SEQ_TIME, SEQ_UNIT, PREDEFINED_EVENTS, LOG_LEVEL, TIME_UNIT
from parser import ASTNode
from utils import log_print, MyTemplate, bt, ListTemplate, log_info
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
            log_print(f"Define new counter <{name}>")
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
            raise Exception(f"Policy {sym.name} redefined")
        self.symbols[sym.name] = sym

    def resolve(self, name):
        if name in self.symbols:
            return self.symbols[name]
        else:
            raise Exception("Symbol not exist")

    def __str__(self):
        return f"GlobalScope: {self.symbols}"


class Policy:
    def __init__(self, name):
        self.name = name
        self.sql_statements = []

    def add_sql(self, statement):
        self.sql_statements.append(statement)

    def __str__(self):
        ans = f"<{self.name}>:"
        for s in self.sql_statements:
            ans += f"\n> {s}"
        return ans


def get_template(name):
    t_map = {
        "SELECT": MyTemplate("SELECT $PROJ$ FROM $TABLE$ WHERE $CONDITION$"),
        "PROJ": MyTemplate("SELECT $PROJ$ FROM $TABLE$"),
        "CREATE_VIEW": MyTemplate("CREATE VIEW $NAME$ AS ( $BODY$ )"),
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
        "WINDOW": MyTemplate("""SELECT $PROJ$,TUMBLE_START(rowtime, INTERVAL $INTERVAL$) AS starttime 
FROM $TABLE$ 
GROUP BY $KEY$,TUMBLE(rowtime, INTERVAL $INTERVAL$)"""),
        "TOPN": MyTemplate("""SELECT $PROJ$ FROM
(
   SELECT $PROJ$,
   ROW_NUMBER() OVER(PARTITION BY $KEY$ ORDER BY $ORDER$ DESC) as rownum
   FROM $TABLE$
)
WHERE rownum = $N$ """),
        "JOIN": MyTemplate("""SELECT $PROJ$ 
FROM $LEFT$ $JOIN_TYPE$ $RIGHT$
ON $LEFT$.$KEY$ = $RIGHT$.$KEY$"""),
        "JOIN_WHERE":MyTemplate("""SELECT $PROJ$ 
FROM $LEFT$ $JOIN_TYPE$ $RIGHT$
ON $LEFT$.$KEY$ = $RIGHT$.$KEY$ WHERE $CONDITION$"""),
    }

    return t_map[name]


class ASTVisitor:
    def __init__(self):
        self.counters = SymbolCounter()
        self.policies = {}

    def __reset_policy(self):
        self.event_table = None
        self.policy = Policy(None)
        self.symbol_table = SymbolTable()
        self.event = None
        self.event_table = None
        self.condition_table=None

    def __define_table(self, name, sql_temp):
        self.symbol_table.define(Symbol(name, SYMBOL_TYPE.TABLE, {'q': sql_temp.get_code()}))

    def __math_cal(self, a, op, b):
        d = {"+": a + b, "-": a - b, '*': a * b, '/': a / b}
        return d[op]

    def create_view(self, sql_template, t_name, **kwargs):
        template_view = get_template("CREATE_VIEW") \
            .set_value("NAME", bt(t_name)) \
            .set_value("BODY", sql_template.get_code())
        self.policy.add_sql(template_view.get_code())
        self.symbol_table.define(Symbol(t_name, SYMBOL_TYPE.TABLE, {'q': sql_template.get_code(), **kwargs}))
        return t_name

    def get_new_name(self, type):
        t_id = self.counters.inc_counter(type)
        return f"{type.name.lower()}_{t_id}"

    def __getfunc(self, name):
        def default_func(node):
            log_print(f"visit {name}")
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
            self.visit(ps)
        log_print(f"Generated {len(node.children)} policies.")

    def visit_PolicyStatement(self, node: ASTNode):
        self.policy.name = self.visit(node.children[0])
        self.symbol_table.define(Symbol(self.policy.name, SYMBOL_TYPE.POLICY, {'obj': self.policy}))
        for cld in node.children[1:]:
            self.visit(cld)

    def visit_String(self, node: ASTNode):
        log_print("visit String " + node.value)
        return node.value

    def visit_ConditionStatement(self,node:ASTNode):
        stack=[]
        table=self.visit(node.children[0],op=None,prev_table=self.event_table)
        stack.append(table)
        i=1
        while i<len(node.children):
            op=self.visit(node.children[i])
            stack.append(self.visit(node.children[i+1],op=op,prev_table=stack.pop()))
            i+=2

    def visit_And(self,node):
        return "AND"
    def visit_Or(self,node):
        return "OR"

    @log_info
    def visit_SingleCondition(self, node: ASTNode,op,prev_table):
        lhs:tuple=self.visit(node.children[0])
        comp=self.visit(node.children[1])
        rhs:tuple=self.visit(node.children[2])
        if isinstance(lhs,tuple) and isinstance(rhs,tuple):
            key='transid' if self.symbol_table.resolve(lhs[0]).attr['key'] == 'transid' and \
                            self.symbol_table.resolve(rhs[0]).attr['key']=='transid' else 'accountnumber'
            key='accountnumber'
            if self.symbol_table.resolve(lhs[0]).attr['key'] == 'transid':
                id_op=lhs
                if self.symbol_table.resolve(rhs[0]).attr['key']=='transid':
                    key='transid'
            elif self.symbol_table.resolve(rhs[0]).attr['key'] == 'transid':
                id_op='rhs'
            else:
                raise Exception("At least one side of comparison needs to have 'transid' as the key")
            template=get_template("JOIN_WHERE").set_value("PROJ",f"{id_op[0]}.transid AS transid")\
                .set_value("LEFT",lhs[0]).set_value("RIGHT",rhs[0])\
                .set_value("KEY",key).set_value("CONDITION",f"{lhs[0]}.`{lhs[1]}` {comp} {rhs[0]}.`{rhs[1]}`")\
                .set_value("JOIN_TYPE","INNOR JOIN")
            t_name=self.get_new_name(COUNTER_TYPE.COMPARISON)
            self.create_view(template,t_name,key='transid')
        elif isinstance(lhs,tuple):
            template=get_template("SELECT").set_value("PROJ","transid").set_value("TABLE",lhs[0])\
                .set_value("CONDITION",f"`{lhs[1]}` {comp} {rhs}")
            t_name=self.get_new_name(COUNTER_TYPE.COMPARISON)
            self.create_view(template,t_name,key='transid')
        else:
           raise Exception("The left side of comparison must be Query or expression with parameters.")
        if op is None or op=='OR':
            table=self.event_table
        elif op=='AND':
            table=prev_table
        print(op)

        template=get_template("SELECT_IN").set_value("PROJ","*").set_value("TABLE",table)\
                    .set_value("IN_COL","transid").set_value("IN_BODY",get_template("PROJ")
                                                             .set_value("PROJ","transid")
                                                             .set_value("TABLE",t_name).get_code())
        t_name=self.get_new_name(COUNTER_TYPE.CONDITION)
        self.create_view(template,t_name,key='transid')
        return t_name


    def visit_Actions(self, node: ASTNode):
        log_print("visit Actions")

    def visit_Comp(self,node:ASTNode):
        return node.value


    @log_info
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
        self.event = events[0]
        event_sqls = [get_template("PROJ")
                          .set_value("PROJ", "*")
                          .set_value("TABLE", et)
                          .get_code() for et in event_tables]
        template_union = get_template("UNION_ALL").set_list(event_sqls)
        self.event_table = self.create_view(template_union, self.get_new_name(COUNTER_TYPE.EVENT), key='transid')

    def visit_SingleEvent(self, node: ASTNode):
        log_print("visit SingleEvent")
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
                log_print(f"{seq_time} is truncated to {int(seq_time)}", LOG_LEVEL.WARNING)
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
                                  .set_value("PROJ", "accountnumber,rowtime,eventtype")
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
        log_print("visit Channel")
        return node.value

    def visit_Event(self, node: ASTNode):
        log_print("visit Event")
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
        if event != self.event:
            raise Exception(f"Only parameters of last event '{self.event}' can be used")
        return (event, param)

    def visit_Sequence(self, node):
        log_print("visit Sequence")
        res_data = {
            "time": None,
            "event_list": None
        }
        if len(node.children) == 1:
            log_print(f"No SEQ time specified. Use default {SEQ_TIME} {SEQ_UNIT}", LOG_LEVEL.WARNING)
            res_data['time'] = SEQ_TIME
            res_data['event_list'] = self.visit(node.children[0])
        else:
            res_data['time'] = self.visit(node.children[0])
            res_data['event_list'] = self.visit(node.children[1])
        return res_data

    def visit_Digits(self, node):
        log_print("visit Digits")
        return node.value

    def visit_Name(self, node):
        return node.value

    def visit_Query(self, node):
        func_name = self.visit(node.children[0])['str']
        params = self.visit(node.children[1])
        t_name, value_name = BuiltInFuncs.call_func(func_name, params, self)
        return t_name, value_name

    def __cal_op(self, left, op, right):
        print(left, op, right)
        if isinstance(left, float) and isinstance(right, float):
            return self.__math_cal(left, op, right)
        if isinstance(left, tuple) and isinstance(right, tuple):
            id_operator = left if self.symbol_table.resolve(left[0]).attr['key'] == 'transid' else right
            template = get_template("JOIN").set_value("PROJ",
                                                      f"{id_operator[0]}.transid AS transid, {left[0]}.`{left[1]}`"
                                                      f" {op} {right[0]}.`{right[1]}` AS `result`") \
                .set_value("LEFT", left[0]).set_value("RIGHT", right[0]) \
                .set_value("KEY", "accountnumber") \
                .set_value("JOIN_TYPE", "INNOR JOIN")
            t_name = self.get_new_name(COUNTER_TYPE.MATH)
            self.create_view(template, t_name, key='transid')
            return t_name, 'result'
        if isinstance(right, tuple):
            t = left
            left = right
            right = t

        if isinstance(left, tuple):
            keys = "accountnumber,transid" if self.symbol_table.resolve(left[0]).attr[
                                                  'key'] == 'transid' else "accountnumber"
            template = get_template("PROJ").set_value("PROJ", f"{keys},`{left[1]}` {op} {right} AS `result`") \
                .set_value("TABLE", left[0])
            t_name = self.get_new_name(COUNTER_TYPE.MATH)
            self.create_view(template, t_name, key=self.symbol_table.resolve(left[0]).attr['key'])
            return t_name, 'result'

    def __cal_expression(self, node):
        result_stack = []
        result_stack.append(self.visit(node.children[0]))
        i = 1
        while i < len(node.children):
            op = self.visit(node.children[i])
            rhs = self.visit(node.children[i + 1])
            res = self.__cal_op(result_stack.pop(), op, rhs)
            print(res)
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
        log_print("visit EventSeq")
        event_list = []
        for c in node.children:
            event_list.append(self.visit(c))
        return event_list


class BuiltInFuncs:
    funcs = {
        'TOTALDEBIT': {
            "param_type": [('Channel', 'Digits'), ('ChannelList', 'Digits'),
                           ('Channel',), ("ChannelList",)],
        }
    }

    @classmethod
    def verify_params(cls, func_name, params):
        param_types = cls.funcs[func_name]['param_type']
        ok = False
        for _params in param_types:
            given_params = tuple(c['type'] for c in params)
            if given_params == _params:
                ok = True
                break
        if not ok:
            raise Exception(f"Parameters do not match. Parameter types of '{func_name}' is ({param_types}).")

    @classmethod
    def totaldebit(cls, params, visitor: ASTVisitor):
        if params[0]['type'] == "Channel":
            channel = params[0]['value']
            table_name = f"{channel}_transfer"
            try:
                visitor.symbol_table.resolve(table_name)
            except:
                t = get_template("SELECT").set_value("PROJ", "*").set_value("TABLE", "transfer") \
                    .set_value("CONDITION", f"channel='{channel}'")
                visitor.create_view(t, table_name, key='transid')
        else:
            table_name = '_'.join(params[0]['value']) + "_transfer"
            try:
                visitor.symbol_table.resolve(table_name)
            except:
                condition_str = " OR ".join([f"channel='{c}'" for c in params[0]['value']])
                t = get_template("SELECT").set_value("PROJ", "*").set_value("TABLE", "transfer") \
                    .set_value("CONDITION", condition_str)
                visitor.create_view(t, table_name, key='transid')

        time = int(params[1]['value']) if len(params) == 2 else 1
        t_name = visitor.get_new_name(COUNTER_TYPE.TOTALDEBIT)
        template = get_template("WINDOW").set_value("PROJ", "accountnumber, SUM(value) AS totaldebit") \
            .set_value("TABLE", table_name) \
            .set_value("KEY", "accountnumber") \
            .set_value("INTERVAL", f"'{time}' DAY")
        visitor.create_view(template, t_name, key='accountnumber')
        template = get_template("TOPN").set_value("PROJ", "accountnumber, totaldebit") \
            .set_value("KEY", "accountnumber") \
            .set_value("ORDER", "starttime") \
            .set_value("TABLE", t_name) \
            .set_value("N", '1')
        t_name = visitor.get_new_name(COUNTER_TYPE.TOTALDEBIT)
        visitor.create_view(template, t_name, key='accountnumber')
        return t_name, 'totaldebit'

    @classmethod
    def call_func(cls, name, params, visitor):
        cls.verify_params(name, params)
        return getattr(cls, name.lower())(params, visitor)


if __name__ == '__main__':
    def abc(a, b, c):
        print(a, b, c)


    def test1(**kwargs):
        abc(**kwargs)


    test1(a=1, b=2, c=3)
