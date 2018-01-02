import redis


def check_user(redis_url, sender_id):
    """
    Check user requests from the past minute; limit to 4 per minute.
    If the limit is exceeded, return the remaining wait time.
    Otherwise, return 0.
    """
    r = redis.from_url(redis_url)
    cur_time = int(r.time()[0])
    if r.exists(sender_id):
        count_time = int(r.lindex(sender_id, 0))
        count = int(r.lindex(sender_id, 1)) + 1
        if abs(cur_time - count_time) < 60:
            r.lset(sender_id, 1, count)
        else:
            r.lset(sender_id, 0, cur_time)
            r.lset(sender_id, 1, 1)
        print('sender_id {0} has requested {1} time(s) in the past minute'.format(sender_id, count))
        return 60 + count_time - cur_time if count >= 4 else 0
    else:
        print('Adding sender_id {0}'.format(sender_id))
        r.lpush(sender_id, 1, cur_time)
        return 0


def check_departures(redis_url, stop_id):
    """Return previous text if last update was less than a minute ago"""
    print('Checking redis for stop_id {0}'.format(stop_id))
    r = redis.from_url(redis_url)
    cur_time = int(r.time()[0])
    if r.exists(stop_id):
        if abs(cur_time - int(r.lindex(stop_id, 0))) < 60:
            print('Already up-to-date')
            message_text = r.lindex(stop_id, 1)
            return message_text.decode(encoding='utf-8')
    return False


def flush_redis(redis_url):
    """Flush redis from the first call of each day after 6 AM CST"""
    r = redis.from_url(redis_url)
    cur_time = int(r.time()[0])
    cur_day = cur_time - (cur_time % 86400) - 43200  # sets to 6 AM CST
    if r.exists('flush_time'):
        if cur_day != int(r.get('flush_time')):
            print('Flushing redis')
            r.flushdb()
            print('Setting last flush time to {0}'.format(cur_day))
            r.set('flush_time', cur_day)
    else:
        print('Setting last flush time to {0}'.format(cur_day))
        r.set('flush_time', cur_day)  # in case redis is externally flushed


def update_departures(redis_url, stop_id, message_text):
    """Update departures in the redis"""
    print('Setting redis key')
    r = redis.from_url(redis_url)
    cur_time = int(r.time()[0])
    r.lset(stop_id, 0, cur_time)
    r.lset(stop_id, 1, message_text)
