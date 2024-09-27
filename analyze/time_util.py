import time
import calendar
import datetime, pytz

epoch = datetime.datetime.utcfromtimestamp(0)
def time_epoch_utc_dt(dt):
    return (dt - epoch).total_seconds()

def get_offset_from_tz(tz):
    now = datetime.datetime.now(pytz.timezone(tz))
    return now.utcoffset().total_seconds()/3600

# returns epoch time for the given time string in UTC/GMT time zone
def time_epoch_utc(time_str):
    return calendar.timegm(time.strptime(time_str, "%Y-%m-%d-%H-%M-%S"))

# returns time string in UTC time zone for the given epoch time
def time_str_cass_utc(time_epoch):
    return time.strftime("%Y-%m-%d %H:%M:%S.000", time.gmtime(time_epoch))

# returns time string in UTC time zone for the given epoch time
def time_str_utc(time_epoch):
    return time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime(time_epoch))

# returns time string (without seconds) in UTC time zone for the given epoch time
def time_str_sec_utc(time_epoch):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time_epoch))

# returns time string (without seconds) in UTC time zone for the given epoch time
def time_str_nosec_utc(time_epoch):
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(time_epoch))

# returns date string in UTC time zone for the given epoch time
def time_str_date_utc(time_epoch):
    return time.strftime("%Y-%m-%d", time.gmtime(time_epoch))

# returns date string in UTC time zone for the given epoch time
def time_str_mdate_utc(time_epoch):
    return time.strftime("%Y%b%d", time.gmtime(time_epoch))

# returns short date string (Mmmdd) in UTC time zone for the given epoch time
def time_str_sdate_utc(time_epoch):
    return time.strftime("%b%d", time.gmtime(time_epoch))

# returns date string with weekday (Mmmdd (Www))in UTC time zone for the given epoch time
def time_str_wdate_utc(time_epoch):
    return time.strftime("%b%d (%a)", time.gmtime(time_epoch))

# returns YYMM in UTC time zone for the given epoch time
def time_str_yymm_utc(time_epoch):
   return time.strftime("%Y%m", time.gmtime(time_epoch))[2:]

# returns time string (without date) in UTC time zone for the given epoch time
def time_str_nodate_utc(time_epoch):
    return time.strftime("%H:%M:%S", time.gmtime(time_epoch))

# returns MMDDYYYY in UTC time zone for the given epoch time
def time_str_mmddyyyy_utc(time_epoch):
    return time.strftime("%m%d%Y", time.gmtime(time_epoch))

# returns YYYYMMDD in UTC time zone for the given epoch time
def time_str_yyyymmdd_utc(time_epoch):
    return time.strftime("%Y%m%d", time.gmtime(time_epoch))

# returns YYYY-MM-DD in UTC time zone for the given epoch time
def time_str_yyyy_mm_dd_utc(time_epoch):
    return time.strftime("%Y-%m-%d", time.gmtime(time_epoch))

