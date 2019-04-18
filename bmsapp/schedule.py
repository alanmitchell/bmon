""" This module holds the Schedule class.  The Schedule class identifies time periods
when a facility is occupied and unoccupied.
"""
import datetime
import pytz
from dateutil import parser


class Schedule:
    """ This class represents an occupied/unoccupied schedule for a facility.
    """

    def __init__(self, schedule_text, tz_name):
        """ Constructs a Schedule object.

        'schedule_text' is a string that describes the occupied periods
            of the schedule.  The format is described below.

        'tz_name' is the name of the timezone (as a string) where the facility
            is located.  'tz_name' must be available in the pytz timezone database.
            An example value is 'US/Alaska'.

        'schedule_text' formatting.  Lines like the following are valid:

            M-F: 8a-5p
            Tu, Th : 6:30p - 7p, 8p - 9:45p

        - Abbreviations for day names are allowed.
        - It is the user's responsibility to ensure that occupied periods do not overlap.

        - Seasonal scheduling is not currently supported.

        """

        # Create a timezone object and store for later use.
        self.tz = pytz.timezone(tz_name)

        schedule_dictionary = {}

        # Parse the schedule description
        for schedule_line in schedule_text.splitlines():

            # ignore blank lines
            if len(schedule_line.strip()) == 0:
                continue

            # Split on first colon into days and times
            schedule_days_text, schedule_times_text = schedule_line.split(':', 1)

            # Parse the days
            days_list = []
            for schedule_day_range in [text.strip() for text in schedule_days_text.split(',')]:
                if '-' in schedule_day_range:
                    schedule_start_day, schedule_end_day = schedule_day_range.split('-', 1)
                    day_index = self.__parse_day_text(schedule_start_day)
                    while True:
                        days_list.append(day_index)
                        if day_index == self.__parse_day_text(schedule_end_day):
                            break
                        else:
                            day_index = (day_index + 1) % 7
                else:
                    days_list.append(self.__parse_day_text(schedule_day_range))

            # Parse the times
            times_list = []
            for schedule_time_range in [text.strip() for text in schedule_times_text.split(',')]:
                schedule_start_time, schedule_end_time = schedule_time_range.split('-', 1)
                times_list.append((parser.parse(schedule_start_time).time(), parser.parse(schedule_end_time).time()))

            # Add the days and times to the schedule dictionary
            day_time_dictionary = dict.fromkeys(days_list, times_list)
            for day in list(day_time_dictionary.keys()):
                if day in schedule_dictionary:
                    schedule_dictionary[day] = schedule_dictionary[day] + day_time_dictionary[day]
                else:
                    schedule_dictionary[day] = day_time_dictionary[day]

        # Set the definition for the schedule
        self.definition = schedule_dictionary

        # Store a list of occupied days ---
        # "Predominantly occupied" means that the number of occupied hours in that day are more than 65% of
        # the occupied hours in the most occupied day of the week.  So, if Monday has 12 occupied hours and
        # is the most occupied day of the week, any day that is occupied for mor than 7.8 hours is considered
        # "Predominantly occupied".

        max_occupied_hours = max([self.__sum_occupied_hours(day_index) for day_index in range(0, 7)])
        self.predominantly_occupied_days = [day_index for day_index in range(0, 7)
                                            if self.__sum_occupied_hours(day_index) > (max_occupied_hours * 0.65)]

    def __sum_occupied_hours(self, day_index):
        """ Returns the total number of occupied hours for the schedule in a given day """

        if day_index in self.definition:
            occupied_times = self.definition[day_index]
            return sum((datetime.datetime.combine(datetime.date.today(), end_time) -
                        datetime.datetime.combine(datetime.date.today(), start_time)).seconds
                       for start_time, end_time in occupied_times) / 60.0 / 60.0

        return 0.0

    @staticmethod
    def __parse_day_text(day_text):
        """ Returns a day index from the text of a day name """

        # Dictionary mapping day names to indices
        # days_dict = dict([(x.strftime('%A'), x.weekday()) for x in [datetime.date(2001, 1, i) for i in range(1, 8)]])
        days_dict = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}

        for day_name in list(days_dict.keys()):
            if day_name.startswith(day_text.capitalize()):
                return days_dict[day_name]

    def is_occupied(self, ts, resolution='exact'):
        """ Returns True if the Unix timestamp, 'ts', falls within an occupied
        period identified by this schedule.  Returns False otherwise.
        If 'resolution' is 'exact', 'ts' is judged against the exact schedule;
        if 'resolution' is 'day', the function returns True if 'ts' falls on a
        'predominantly occupied' day (see __init__() constructor for further 
        info).
        """

        # convert the timestamp 'ts' to a Python datetime object in the facility's time zone
        dt = datetime.datetime.fromtimestamp(ts, self.tz)

        if resolution=='exact':
            # test to see if there is an entry in the schedule dictionary for the day and time
            if dt.weekday() in self.definition:
                # retrieve the occupied times for the day
                occupied_times = self.definition[dt.weekday()]

                for start_time, end_time in occupied_times:
                    if start_time < dt.time() < end_time:
                        return True

            # Return False if we haven't already returned with True
            return False

        else:
            # return True if ts is in predominantly occupied day.
            return dt.weekday() in self.predominantly_occupied_days

    def occupied_periods(self, ts_start, ts_end, resolution='exact'):
        """ Returns a list of two-tuples identifying all of the occupied periods
        falling in the range from 'ts_start' to 'ts_end', which are both Unix
        timestamps.  The format of the return list is:
            [ (1419276095, 1419276200), (1419276300, 1419276500), etc ]
        Each tuple gives the start and stop of an occupied period, using Unix
        timestamps.
        The 'resolution' parameter has two possible values:
            'exact': occupied / unoccupied boundaries are at the exact times
                specified in the schedule.
            'day': occupied / unoccupied boundaries are placed on day boundaries;
                the returned tuples identify occupied days but do not give within
                day resolution of occupied periods.
        """

        periods_list = []

        # Loop through the timestamp range by day
        for ts in range(int(ts_start), int(ts_end) + 1, 60 * 60 * 24):
            dt = datetime.datetime.fromtimestamp(ts, self.tz)

            # test to see if there is an entry in the schedule dictionary for the day and time
            if dt.weekday() in self.definition:
                if resolution == 'exact':
                    # retrieve the occupied times for the day
                    occupied_times = self.definition[dt.weekday()]
                else:
                    if dt.weekday() in self.predominantly_occupied_days:
                        occupied_times = [(datetime.time(0), datetime.time(23, 59, 59))]
                    else:
                        occupied_times = []

                # convert the start and end times to timestamps
                for start, end in occupied_times:
                    start_ts = self.__dt_to_ts(dt.replace(hour=start.hour, minute=start.minute, second=start.second))
                    end_ts = self.__dt_to_ts(dt.replace(hour=end.hour, minute=end.minute, second=end.second))
                    if end_ts >= ts_start and start_ts <= ts_end:
                        if start_ts < ts_start:
                            start_ts = ts_start
                        if end_ts > ts_end:
                            end_ts = ts_end
                        periods_list.append((start_ts, end_ts))

        # merge contiguous occupied periods
        dissolved_list = []
        start_ts = None
        for periods_list_index in range(len(periods_list)):
            period_start, period_end = periods_list[periods_list_index]
            if start_ts is None:
                start_ts = period_start
            try:
                next_start = periods_list[periods_list_index + 1][0]
            except IndexError:
                next_start = float('inf')
            if next_start > (period_end + 1):
                dissolved_list.append((start_ts, period_end))
                start_ts = None

        return dissolved_list

    def __dt_to_ts(self, date_time):
        """ Returns a timestamp corresponding to a Python datetime """
        date_time_delta = date_time - datetime.datetime.fromtimestamp(0, self.tz)
        return date_time_delta.seconds + (date_time_delta.days * 24 * 60 * 60)


if __name__ == '__main__':
    """ Run some tests on the schedule class """
    description = 'M-F: 11a-5p\nTu, Th : 6:30p - 7p, 8p - 9:45p\nSat: 11:00-1PM'
    schedule_object = Schedule(description, 'US/Alaska')

    dt_now = datetime.datetime.now()
    dt_delta = dt_now - datetime.datetime.fromtimestamp(0)
    dt_ts = dt_delta.seconds + (dt_delta.days * 24 * 60 * 60)

    print(str(schedule_object.definition))
    print(schedule_object.predominantly_occupied_days)
    print(schedule_object.is_occupied(dt_ts))
    op = schedule_object.occupied_periods(dt_ts, dt_ts + (60 * 60 * 24 * 7), 'exact')
    print([(datetime.datetime.fromtimestamp(start_dt_ts), datetime.datetime.fromtimestamp(end_dt_ts))
           for start_dt_ts, end_dt_ts in op])
