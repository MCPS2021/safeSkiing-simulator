import curses
import datetime
import json
import sys
import time

from paho.mqtt import publish

from classes.SafeSkiingSimulator import SafeSkiingSimulator
from classes.SkiPass import SkiPass

def gui(stdscr, a , b):
    #stdscr = curses.initscr()
    print (a, b)
    while True:
        stdscr.addstr(0,0,"Slope {}".format(a))
        stdscr.addstr(1,0,"Slope {}".format(b))
        stdscr.move(curses.LINES - 1, 0)
        stdscr.refresh()
        time.sleep(1)

def test_mqtt(hostname):
    publish.single("/test1/test", str(datetime.datetime.now()), hostname=hostname, qos=2)

if __name__ == '__main__':
    with open('config.json') as f:
        config = json.load(f)

    sim = SafeSkiingSimulator(config,mqtt_broker_host="192.168.1.150",initial_people=5)

    #for slope in sim.slopes:
    #    print(slope.get_info())


    sim.simulate(gui_enabled=True, n_steps=1000,sleep_time=3)

    #curses.wrapper(gui, 2, 2)