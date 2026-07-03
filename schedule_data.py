DEFAULT_START_HOUR = 9
DEFAULT_END_HOUR = 24
DEFAULT_STEP_HOURS = 0.5
DAY_NAMES = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']


def formatTimeLabel(hour, minute):
    suffix = 'AM' if hour < 12 else 'PM'
    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12
    return f'{display_hour}:{minute:02d} {suffix}'


def buildTimeLabels(start, end, step):
    labels = []
    t = start
    while t < end:
        mins = int((t % 1) * 60)
        labels.append(formatTimeLabel(int(t) % 24, mins))
        t += step
    return labels


def buildEmptyWeek(day_count, slot_count):
    return [[set() for i in range(slot_count)] for j in range(day_count)]


def initializeScheduleData(data):
    data.start = DEFAULT_START_HOUR
    data.end = DEFAULT_END_HOUR
    data.step = DEFAULT_STEP_HOURS
    data.slots = int((data.end - data.start) / data.step)
    data.times = buildTimeLabels(data.start, data.end, data.step)
    data.week = buildEmptyWeek(len(DAY_NAMES), data.slots)
    data.rows = len(DAY_NAMES)
    data.cols = len(data.week[0])
    data.name = ''
    data.names = []
    data.groups = dict()
    data.day_names = DAY_NAMES
