from enum import IntEnum
import re

from pywikibot import WbTime


class WbTimePrecision(IntEnum):
    DAY = 11
    MONTH = 10
    YEAR = 9

    @staticmethod
    def from_str(s:str):
        y, m, d = re.match(re.match(WB_TIME_REGEX, s).group(1, 2, 3))
        if int(d) != 0:
            return WbTimePrecision.DAY
        if int(m) != 0:
            return WbTimePrecision.MONTH
        return WbTimePrecision.YEAR


WB_TIME_REGEX = r"([-+]?\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)Z"


def time_match(time1:WbTime, time2:WbTime):
    precision = min(time1.precision, time2.precision)
    if precision >= WbTimePrecision.YEAR and time1.year != time2.year:
        return False
    if precision >= WbTimePrecision.MONTH and time1.month != time2.month:
        return False
    if precision >= WbTimePrecision.DAY and time1.day != time2.day:
        return False
    return True
