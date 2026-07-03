import datetime
import re
from math import ceil, floor

from icalendar import Calendar


def parseRecurringBusySlots(ics_data, day_names, start_hour, step_hours,
                            slot_count=None):
    busy_slots = set()
    try:
        calendar = Calendar.from_ical(_normalizeIcsData(ics_data))
        for event in calendar.walk('VEVENT'):
            start = _eventDateTime(event.get('dtstart'))
            end = _eventDateTime(event.get('dtend'))
            if start is None:
                continue
            if end is None:
                end = start + datetime.timedelta(hours=step_hours)
            if isinstance(start, datetime.date) and not isinstance(start, datetime.datetime):
                continue
            if isinstance(end, datetime.date) and not isinstance(end, datetime.datetime):
                continue

            day_index = start.weekday()
            start_idx = _slotIndex(start, start_hour, step_hours, floor)
            end_idx = _slotIndex(end, start_hour, step_hours, ceil)
            _addBusySlot(
                busy_slots, day_index, start_idx, end_idx, len(day_names),
                slot_count
            )
    except ValueError:
        pass

    for busy_slot in _parseBydayBusySlots(
        ics_data, day_names, start_hour, step_hours, slot_count
    ):
        busy_slots.add(busy_slot)
    return sorted(busy_slots)


def _normalizeIcsData(ics_data):
    if isinstance(ics_data, bytes):
        text = ics_data.decode('utf-8-sig', errors='replace')
    else:
        text = ics_data
    text = re.sub(r'(?m)^(BEGIN|END):([A-Z]+)\s+$', r'\1:\2', text)
    return text


def _parseBydayBusySlots(ics_data, day_names, start_hour, step_hours,
                         slot_count):
    if isinstance(ics_data, bytes):
        ics_data = ics_data.decode('utf-8-sig', errors='replace')
    pat = re.compile(
        r'DTSTART(?:;[^:]*)?:\d+?T(\d\d)(\d\d).*?'
        r'DTEND(?:;[^:]*)?:\d+?T(\d\d)(\d\d).*?'
        r'BYDAY=([^;\r\n]+)',
        re.DOTALL
    )
    busy_slots = set()
    for (start_h, start_m, end_h, end_m, days) in re.findall(pat, ics_data):
        start_idx = floor(
            (int(start_h) - start_hour + int(start_m) / 60) / step_hours
        )
        end_idx = ceil(
            (int(end_h) - start_hour + int(end_m) / 60) / step_hours
        )
        for day in days.split(','):
            if day in day_names:
                _addBusySlot(
                    busy_slots, day_names.index(day), start_idx, end_idx,
                    len(day_names), slot_count
                )
    return busy_slots


def _eventDateTime(value):
    if value is None:
        return None
    return value.dt


def _slotIndex(value, start_hour, step_hours, round_func):
    hour_value = (
        value.hour
        + value.minute / 60
        + value.second / 3600
    )
    return round_func((hour_value - start_hour) / step_hours)


def _addBusySlot(busy_slots, day_index, start_idx, end_idx, day_count,
                 slot_count):
    if slot_count is not None:
        start_idx = max(0, min(start_idx, slot_count))
        end_idx = max(0, min(end_idx, slot_count))
    if 0 <= day_index < day_count and start_idx < end_idx:
        busy_slots.add((day_index, start_idx, end_idx))
