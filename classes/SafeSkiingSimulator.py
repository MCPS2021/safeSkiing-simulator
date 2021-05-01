import curses
import random
import sys
import threading
import time

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import paho.mqtt.publish as publish

from classes.SkiPass import SkiPass
from classes.Slope import Slope
from exceptions import NoBackgroundImage
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

    def __init__(self, config=None, mqtt_broker_host=None, initial_people=100):
        c_slopes = config['slopes']

        try:
            self.background_image = config['background-image']
        except:
            self.background_image = None

        self.slopes = []
        self.mqtt_broker_host = mqtt_broker_host
        self.slopes_labels = {}

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
                print("With slope time: {}".format(slope_time))
                self.slopes.append(
                    Slope(c_slope['name'], c_slope['station_name'], slope_time))

                # adding label coordinates
                self.slopes_labels[c_slope['name']] = c_slope['label']

            for slope in self.slopes:
                # get the slope exits defined in the conf
                print("Getting the exits for slope {}".format(slope.name))
                exits = get_exits_by_name(c_slopes, slope.name)
                print("Exits: {}".format(exits))

                # replace the slope names in the exits config, with the actual slope object created above
                result = {"slopes": [get_slope_by_name(self.slopes, name) for name in exits['slopes']],
                          "distribution": exits['distribution'], "ski_lifts_capacities": exits['ski_lifts_capacities']}
                slope.set_exits(result)

        else:
            raise BadSlopesException()

        # init people on the root
        people = [SkiPass(get_random_uuid()) for n in range(0, initial_people)]
        for p in people:
            get_slope_by_name(self.slopes, 'root').push(p)

    def get_slopes_status(self, slope_name=None):
        for slope in self.slopes:

            if slope_name is not None and slope.name != slope_name:
                continue

            print("Slope {}".format(slope.name))
            print("Slope Queue: {}".format(slope.get_slope_queue()))
            print("tot {}".format(len(slope.get_slope_queue())))
            print("Ski Lift Queues: {}".format(slope.get_ski_lifts_queues()))
            print("#" * 50)

    def simulate(self, gui_enabled=True, n_steps=1, sleep_time=1):
        if gui_enabled:
            # create GUI app and window
            app, window = self.build_window()
            # create the thread that will update the labels on the GUI
            updating_thread = threading.Thread(target=self.simulate_gui, args=(window, n_steps, sleep_time,))
            # start the thread
            updating_thread.start()
            # exec the GUI
            sys.exit(app.exec())

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

    def simulate_gui(self, window, n_steps, sleep_time):
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

            # update labels
            for slope in self.slopes:
                # take the label object (filtering by name)
                label_object = window.findChildren(QLabel, name=slope.name)
                if len(label_object) == 0:
                    continue
                # set the text
                label_object[0].setText(str(len(slope.ski_lift_queue)))

            time.sleep(sleep_time)

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
            all_UUIDs = ""
            for person in slope.ski_lift_queue:
                all_UUIDs += str(person.uuid) + "," + str(person.battery) + ";"
            all_UUIDs = all_UUIDs[:-1]

            # send the two MQTT topics
            publish.single("/{}/totalPeople".format(slope.station_name), str(len(slope.ski_lift_queue)),
                           hostname=self.mqtt_broker_host)
            publish.single("/{}/UUIDs".format(slope.station_name), all_UUIDs, hostname=self.mqtt_broker_host)

    def build_window(self):
        print("Creating the GUI")
        # initialize GUI application
        app = QApplication(sys.argv)

        # window and settings
        window = QWidget()
        window.setWindowTitle("Safe Skiing Simulator")
        # window position and dimension
        window.setGeometry(50, 50, 824, 707)
        # check if the background image was specified in the config
        if self.background_image is None:
            raise NoBackgroundImage
        #set the background image
        window.setStyleSheet(
            "background-image: url("+self.background_image+"); background-repeat: no-repeat; background-position: center;")

        for label in self.slopes_labels:
            print ("Creating label", label)
            # create the label
            slope_label = QLabel(parent=window)
            slope_label.setFont(QFont('Arial', 10, QFont.Bold))
            slope_label.setStyleSheet("color: #ff0000;")
            # move the label in the coords indicated in the config file
            slope_label.move(self.slopes_labels.get(label)[0], self.slopes_labels.get(label)[1])
            # set as label name the slope name
            # in this way we can access it later on through
            # window.findChildren(QLabel, name="label1"):
            slope_label.setObjectName(label)
        window.show()
        return app, window