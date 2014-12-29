'''This module holds the Schedule class.  The Schedule class identifies time periods
when a facility is occupied and unoccupied.
'''
import datetime
import pytz
from dateutil import parser

class Schedule:
    '''This class represents an occupied/unoccupied schedule for a facility.
    '''

    def __init__(self, schedule_text, tz_name):
        '''Constructs a Schedule object.

        'schedule_text' is a string that describes the occupied periods
            of the schedule.  The format is described below.

        'tz_name' is the name of the timezone (as a string) where the facility
            is located.  'tz_name' must be available in the pytz timezone database.
            An example value is 'US/Alaska'.

        'schedule_text' formatting.  Lines like the following are valid:

            M-F: 8a-5p
            Tu, Th : 6:30p - 7p, 8p - 9:45p

        Abbreviations for day names are allowed.
        Seasonal scheduling is not currently supported.

        '''

        # Create a timezone object and store for later use.
        self.tz = pytz.timezone(tz_name)

        schedule_dictionary = {}

        # Parse the schedule description
        for schedule_line in  schedule_text.splitlines():

            # Split on first colon into days and times
            schedule_days_text,schedule_times_text = schedule_line.split(':',1)

            # Parse the days
            days_list = []
            for schedule_day_range in [text.strip() for text in schedule_days_text.split(',')]:
                if '-' in schedule_day_range:
                    schedule_start_day,schedule_end_day = schedule_day_range.split('-',1)
                    for day_index in range(self.__parse_day_text(schedule_start_day),
                                           self.__parse_day_text(schedule_end_day) + 1):
                        days_list.append(day_index)
                else:
                    days_list.append(self.__parse_day_text(schedule_day_range))

            # Parse the times
            times_list = []
            for schedule_time_range in [text.strip() for text in schedule_times_text.split(',')]:
                schedule_start_time,schedule_end_time = schedule_time_range.split('-',1)
                times_list.append((parser.parse(schedule_start_time).time(),parser.parse(schedule_end_time).time()))

            # Add the days and times to the schedule dictionary
            day_time_dictionary = dict.fromkeys(days_list, times_list)
            for day in day_time_dictionary.keys():
                if schedule_dictionary.has_key(day):
                    schedule_dictionary[day] = schedule_dictionary[day] + day_time_dictionary[day]
                else:
                    schedule_dictionary[day] = day_time_dictionary[day]

        # Set the definition for the schedule
        self.definition = schedule_dictionary

    def __parse_day_text(self, day_text):
        '''Returns a day index from the text of a day name'''

        # Dictionary mapping day names to indices
        # days_dict = dict([(x.strftime('%A'), x.isoweekday()) for x in [datetime.date(2001, 1, i) for i in range(1, 8)]])
        days_dict = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
                     'Thursday': 4, 'Friday': 5, 'Saturday': 6}

        for day_name in days_dict.keys():
            if day_name.startswith(day_text):
                return days_dict[day_name]

    def is_occupied(self, ts):
        '''Returns True if the Unix timestamp, 'ts', falls within an occupied
        period identified by this schedule.  Returns False otherwise.
        '''

        # convert the timestamp 'ts' to a Python datetime object in the facility's time zone
        dt = datetime.datetime.fromtimestamp(ts, self.tz)

        # test to see if there is an entry in the schedule dictionary for the day and time
        if self.definition.has_key((dt.isoweekday())):
            # retrieve the occupied times for the day
            occupied_times = self.definition[dt.isoweekday()]

            for start_time,end_time in occupied_times:
                if start_time < dt.time() < end_time:
                    return True

        # Return False if we haven't already returned with True
        return False

    def is_occupied_day(self, ts):
        '''Returns True if the Unix timestamp, 'ts', falls on a day that is 
        "predominantly occupied".  Returns False otherwise.  "Predominantly
        occupied" means that the number of occupied hours in that day are 
        more than 65% of the occupied hours in the most occupied day of
        the week.  So, if Monday has 12 occupied hours and is the most
        occupied day of the week, this function will return True if the
        day of the week that 'ts' falls on has more than 7.8 occupied hours.
        '''
        return True
        
    def occupied_periods(self, ts_start, ts_end):
        '''Returns a list of two-tuples identifying all of the occupied periods
        falling in the range from 'ts_start' to 'ts_end', which are both Unix
        timestamps.  The format of the return list is:
            [ (1419276095, 1419276200), (1419276300, 1419276500), etc ]
        Each tuple gives the start and stop of an occupied period, using Unix
        timestamps.
        '''

        periods_list = []

        # Loop through the timestamp range by day
        for ts in range(int(ts_start), int(ts_end) + 1, 60 * 60 * 24):
            dt = datetime.datetime.fromtimestamp(ts, self.tz)

            # test to see if there is an entry in the schedule dictionary for the day and time
            if self.definition.has_key(dt.isoweekday()):
                # retrieve the occupied times for the day
                occupied_times = self.definition[dt.isoweekday()]

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

        return periods_list

    def __dt_to_ts(self, date_time):
        date_time_delta = date_time - datetime.datetime.fromtimestamp(0, self.tz)
        return  date_time_delta.seconds + (date_time_delta.days * 24 * 60 * 60)

if __name__ == '__main__':
    description = 'M-F: 8a-5p\nTu, Th : 6:30p - 7p, 8p - 9:45p'
    schedule_object = Schedule(description,'US/Alaska')

    print str(schedule_object.definition)
    # print schedule_object.is_occupied(time.time())
    # print schedule_object.occupied_periods(time.time(),time.time() + (60 * 60 * 24 * 3))

