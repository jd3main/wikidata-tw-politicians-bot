from enum import IntEnum
import re

from wikidataintegrator import wdi_core
import pywikibot


class WbTimePrecision(IntEnum):
    DAY = 11
    MONTH = 10
    YEAR = 9

    @staticmethod
    def from_str(s:str):
        y,m,d = re.match(re.match(WB_TIME_REGEX, s).group(1,2,3))
        if int(d) != 0:
            return WbTimePrecision.DAY
        if int(m) != 0:
            return WbTimePrecision.MONTH
        return WbTimePrecision.YEAR



WB_TIME_REGEX = r"([-+]?\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)Z"

def time_wdi_to_pwb(wdi_time:wdi_core.WDTime):
    return pywikibot.WbTime.fromTimestr(wdi_time.time, precision=wdi_time.precision)
