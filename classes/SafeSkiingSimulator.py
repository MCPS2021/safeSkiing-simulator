import curses
import random
import paho.mqtt.publish as publish

from classes.SkiPass import SkiPass
from classes.Slope import Slope
from exceptions.BadSlopesException import BadSlopesException


def slopes_conf_validator(conf):
    return True


def get_exits_by_name(slopes, name):
    for slope in slopes:
        if slope['name'] == name:
            return slope['exits']


def get_slope_by_name(slopes, name):
    for slope in slopes:
        if slope.name == name:
            return slope


def get_random_uuid():
    uuid = ''
    for i in range(0, 4):
        quartet = ''.join(random.choices('0123456789abcdef', k=4))
        uuid += quartet
    return uuid


class SafeSkiingSimulator:

    def __init__(self, c_slopes=None, mqtt_broker_host=None ,initial_people=100):
        self.slopes = []
        self.mqtt_broker_host = mqtt_broker_host

        # check if passed slopes are correctly formatted
        # and create the slopes
        if slopes_conf_validator(c_slopes):
            for c_slope in c_slopes:

                if c_slope['name'] == 'root':
                    print("Adding root slope..")
                    self.slopes.append(Slope('root', slope_time=(0, 0)))
                    continue

                print("Adding slope {}".format(c_slope['name']))
                slope_time = (c_slope['slope_time']['min'], c_slope['slope_time']['max'])
                print("With slope time: {}, and ski lift capacity {}".format(slope_time, c_slope['ski_lift_capacity']))
                self.slopes.append(Slope(c_slope['name'], c_slope['station_name'],slope_time, c_slope['ski_lift_capacity']))

            for slope in self.slopes:
                # get the slope exits defined in the conf
                print("Getting the exits for slope {}".format(slope.name))
                exits = get_exits_by_name(c_slopes, slope.name)
                print("Exits: {}".format(exits))

                # replace the slope names in the exits config, with the actual slope object created above
                result = {"slopes": [get_slope_by_name(self.slopes, name) for name in exits['slopes']],
                          "distribution": exits['distribution']}
                slope.set_exits(result)

        else:
            raise BadSlopesException()

        # init people on the root
        people = [SkiPass(get_random_uuid()) for n in range(0, initial_people)]
        get_slope_by_name(self.slopes, 'root').set_ski_lift_queue(people)

    def get_slopes_status(self, slope_name=None):
        for slope in self.slopes:

            if slope_name is not None and slope.name != slope_name:
                continue

            print("Slope {}".format(slope.name))
            print("Slope Queue: {}".format(slope.get_slope_queue()))
            print("tot {}".format(len(slope.get_slope_queue())))
            print("Ski Lift Queue: {}".format(slope.get_ski_lift_queue()))
            print("tot {}".format(len(slope.get_ski_lift_queue())))
            print("#" * 50)

    def simulate(self, gui_enabled=True, n_steps=1, sleep_time=1):
        if gui_enabled:
            curses.wrapper(self.simulate_gui, n_steps, sleep_time)
        else:
            for step in range(0, n_steps):
                # pop people form the slopes
                # people exit from ski lift queue and goes to
                # slope queue cache
                for slope in self.slopes:
                    slope.pop()
                # once all the slopes are popped, put the cache items
                # (which are people that was transferred this round)
                # into the real slope queue (with their timer)
                # in this way the slope queue time parameter is used correctly
                for slope in self.slopes:
                    slope.empty_cache()

                print(self.get_slopes_status())

    def simulate_gui(self, stdscr, n_steps, sleep_time):
        for step in range(0, n_steps):
            # pop people form the slopes
            # people exit from ski lift queue and goes to
            # slope queue cache
            for slope in self.slopes:
                slope.pop()
            # once all the slopes are popped, put the cache items
            # (which are people that was transferred this round)
            # into the real slope queue (with their timer)
            # in this way the slope queue time parameter is used correctly
            for slope in self.slopes:
                slope.empty_cache()

            # draw the gui
            self.draw(stdscr)

            stdscr.get_wch()
            # time.sleep(sleep_time)

    def get_slope_by_name(self, name):
        for slope in self.slopes:
            if slope.name == name:
                return slope

    def draw(self, stdscr):
        for i, slope in enumerate(self.slopes):
            stdscr.addstr(i, 0,
                          "Slope {}, Slope Queue: {}, Ski Lift Queue: {}".format(slope.name, len(slope.slope_queue),
                                                                                 len(slope.ski_lift_queue)))
        stdscr.move(curses.LINES - 1, 0)
        stdscr.refresh()

    def publish_MQTT(self):
        for slope in self.slopes:
            if slope.name == 'root':
                continue

            # concatenate all the UUIDs
            all_UUIDs=""
            for person in slope.ski_lift_queue:
                all_UUIDs += str(person.uuid) + "," + str(person.battery) + ";"
            all_UUIDs = all_UUIDs[:-1]

            #send the two MQTT topics
            publish.single("/{}/totalPeople".format(slope.station_name), str(len(slope.ski_lift_queue)), hostname=self.mqtt_broker_host)
            publish.single("/{}/UUIDs".format(slope.station_name), all_UUIDs, hostname=self.mqtt_broker_host)
