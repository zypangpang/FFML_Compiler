from datetime import datetime,timedelta
import sys

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

def get_ms_delta(time_str1,time_str2):
    time1=datetime.strptime(time_str1,TIME_FORMAT)
    time2=datetime.strptime(time_str2,TIME_FORMAT)
    if time1> time2:
        delta=(time1-time2)/timedelta(milliseconds=1)
    else:
        delta=(time2-time1)/timedelta(milliseconds=1)

    print(delta)

if __name__ == '__main__':
    get_ms_delta(sys.argv[1],sys.argv[2])

