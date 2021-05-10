import json
import sys

from classes.SafeSkiingSimulator import SafeSkiingSimulator

if __name__ == '__main__':
    with open('config.json') as f:
        config = json.load(f)
    
    mqtt_host = ""
    if config["docker"] == False:
        gui_enabled = True
        mqtt_host = config["mqtt_broker_host"]
    else:
        gui_enabled = False
        mqtt_host = "mqtt_broker"

    sim = SafeSkiingSimulator(config,mqtt_broker_host=mqtt_host, initial_people=config['initial_people'])

    sim.simulate(gui_enabled=gui_enabled, n_steps=config['n_steps'],sleep_time=config['sleep_time'])
