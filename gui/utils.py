log_str_list=[]

def clear_log():
    log_str_list.clear()

def get_log_list():
    return log_str_list

def add_log(content,level):
    log_str_list.append(level.upper() + ": " + content)
