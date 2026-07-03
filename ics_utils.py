import re
from math import ceil, floor


def parseRecurringBusySlots(ics_data, day_names, start_hour, step_hours):
    pat = re.compile(
        r'DTSTART:\d+?T(\d\d)(\d\d).*?'
        r'DTEND:\d+?T(\d\d)(\d\d).+?BYDAY=(\S+)',
        re.DOTALL
    )
    busy_slots = []
    for (start_h, start_m, end_h, end_m, days) in re.findall(pat, ics_data):
        for day in days.split(','):
            day_index = day_names.index(day)
            start_idx = floor(
                (int(start_h) - start_hour + int(start_m) / 60) / step_hours
            )
            end_idx = ceil(
                (int(end_h) - start_hour + int(end_m) / 60) / step_hours
            )
            busy_slots.append((day_index, start_idx, end_idx))
    return busy_slots
