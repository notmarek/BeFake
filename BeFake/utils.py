import time, datetime

def unix_timestamp():
    return str(int(
        time.mktime(
            datetime.datetime.now()
            .timetuple()
        )
    ))

