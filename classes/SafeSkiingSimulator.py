import random
import sys
import threading
import time

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

        self.config = config

        c_slopes = config['slopes']

        try:
            self.background_image = config['background-image']
        except:
            self.background_image = None

        self.slopes = []
        self.mqtt_broker_host = mqtt_broker_host
        self.ski_lifts_labels = {}
        self.slope_labels = {}

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
                if 'ski_lift_label' in c_slope:
                    self.ski_lifts_labels[c_slope['name']] = c_slope['ski_lift_label']

                # adding slope lables coords
                if 'slope_label' in c_slope:
                    self.slope_labels[c_slope['name']] = c_slope['slope_label']

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
        with open("uuids.csv", "r") as file:
            lines = file.readlines()
        people = [SkiPass(el.strip().split(";")[0], battery=el.strip().split(";")[1]) for el in lines[:initial_people]]
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

                # if a mqtt broker is specified in the config
                if self.mqtt_broker_host is not None:
                    self.publish_MQTT()

                # pop people form the slopes
                # people exit from ski lift queue and goes to
                # slope queue cache
                for slope in self.slopes:
                    slope.pop(mqtt_broker_host = self.mqtt_broker_host)
                # once all the slopes are popped, put the cache items
                # (which are people that was transferred this round)
                # into the real slope queue (with their timer)
                # in this way the slope queue time parameter is used correctly
                for slope in self.slopes:
                    slope.empty_cache()

                print(self.get_slopes_status())
                time.sleep(sleep_time)

    def simulate_gui(self, window, n_steps, sleep_time):

        if not self.config['docker']:
            from PyQt5.QtWidgets import *
            from PyQt5.QtGui import *

        for step in range(0, n_steps):

            # if a mqtt broker is specified in the config
            if self.mqtt_broker_host is not None:
                self.publish_MQTT()

            # pop people form the slopes
            # people exit from ski lift queue and goes to
            # slope queue cache
            for slope in self.slopes:
                slope.pop(mqtt_broker_host=self.mqtt_broker_host)
            # once all the slopes are popped, put the cache items
            # (which are people that was transferred this round)
            # into the real slope queue (with their timer)
            # in this way the slope queue time parameter is used correctly
            for slope in self.slopes:
                slope.empty_cache()

            # update labels
            for slope in self.slopes:
                # take the label object (filtering by name)
                # first the ski lift label then the slope label
                ski_lift_label_object = window.findChildren(QLabel, name=(slope.name + "_ski_lift_label"))
                slope_label_object = window.findChildren(QLabel, name=(slope.name + "_slope_label"))

                # set slope label text
                if len(slope_label_object) == 0:
                    continue

                slope_label_object[0].setText(str(len(slope.slope_queue)))
                slope_label_object[0].adjustSize()

                if len(ski_lift_label_object) == 0:
                    continue
                # set the text of the ski lift queue label
                for exit_idx,exit in enumerate(slope.exits['slopes']):
                    if slope.exits['ski_lifts_capacities'][exit_idx] > 0:
                        ski_lift_label_object[0].setText(str(len(slope.ski_lifts_queues[exit_idx])))
                        ski_lift_label_object[0].adjustSize()
                        break



            time.sleep(sleep_time)

        print("Simulation terminates")

    def get_slope_by_name(self, name):
        for slope in self.slopes:
            if slope.name == name:
                return slope


    def publish_MQTT(self):
        for slope in self.slopes:
            if slope.name == 'root':
                continue

            # concatenate all the UUIDs: UUID,battery;.....
            all_UUIDs = ""

            # take the exit idx of the exit with capacity > 0
            # assuming one only ski lift for each slope
            ski_lift_queue = None
            for exit_idx, exit in enumerate(slope.exits['slopes']):
                if slope.exits['ski_lifts_capacities'][exit_idx] > 0:
                    ski_lift_queue = slope.ski_lifts_queues[exit_idx]
                    break

            # if I did not find the ski lift queue (meaning that no ski lift in this slope)
            # or no people in the queue
            # just skip this slope
            if ski_lift_queue is None:
                continue
            if len(ski_lift_queue) == 0:
                publish.single("/station{}/totalPeople".format(slope.station_name), str(0),
                               hostname=self.mqtt_broker_host, qos=2)
                continue

            # otherwise concat all the UUIDs in the queue
            for person in ski_lift_queue:
                all_UUIDs += str(person.uuid) + "," + str(person.battery) + ";"
            all_UUIDs = all_UUIDs[:-1]

            # send the two MQTT topics
            publish.single("/station{}/totalPeople".format(slope.station_name), str(len(ski_lift_queue)),
                           hostname=self.mqtt_broker_host, qos=2)
            publish.single("/station{}/UUIDs".format(slope.station_name), all_UUIDs, hostname=self.mqtt_broker_host, qos=2)

    def build_window(self):
        if not self.config['docker']:
            from PyQt5.QtWidgets import *
            from PyQt5.QtGui import *

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

        for label in self.ski_lifts_labels:
            print ("Creating ski lift label", label)
            # create the label
            slope_label = QLabel(parent=window)
            slope_label.setFont(QFont('Arial', 15, QFont.Bold))
            slope_label.setStyleSheet("color: #ffffff; background: rgba(0,0,0,0);")
            slope_label.setAutoFillBackground(True);
            # move the label in the coords indicated in the config file
            slope_label.move(self.ski_lifts_labels.get(label)[0], self.ski_lifts_labels.get(label)[1])
            # set as label name the slope name
            # in this way we can access it later on through
            # window.findChildren(QLabel, name="label1"):
            slope_label.setObjectName(label+"_ski_lift_label")

        for label in self.slope_labels:
            print ("Creating slope label", label)
            # create the label
            slope_label = QLabel(parent=window)
            slope_label.setFont(QFont('Arial', 15, QFont.Bold))
            slope_label.setStyleSheet("color: #ff0000; background: rgba(0,0,0,0);")
            # move the label in the coords indicated in the config file
            slope_label.move(self.slope_labels.get(label)[0], self.slope_labels.get(label)[1])
            # set as label name the slope name
            # in this way we can access it later on through
            # window.findChildren(QLabel, name="label1"):
            slope_label.setObjectName(label + "_slope_label")

        window.show()
        return app, window
