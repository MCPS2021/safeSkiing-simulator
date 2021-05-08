import random

import numpy as np
from paho.mqtt import publish


class Slope:
    def __init__(self, name, station_name=None, slope_time=(1,5)):
        self.name = name
        if station_name == None:
            self.station_name = name
        else:
            self.station_name = station_name
        self.slope_queue_cache = []
        self.slope_queue = []
        self.ski_lifts_queues = []
        self.slope_time = slope_time
        self.exits = {}
        self.ski_lifts_capacities = []

    def set_exits(self, exits):
        self.exits = exits
        for exit in self.exits['slopes']:
            self.ski_lifts_queues.append([])

    def pop(self, mqtt_broker_host=None):
        # extract people with timer == 0 from slope queue
        extracted_people = [x['object'] for x in self.slope_queue if x['timer'] == 0]
        # recreate slope queue without people with timer == 0
        self.slope_queue = [x for x in self.slope_queue if x['timer'] != 0]

        # reduce timer of each person in the slope queue
        for item in self.slope_queue:
            item['timer'] -= 1

        # if someone exits from the slope
        if len(extracted_people) > 0:
            # divide people based on the multinomial distribution defined in the exits
            multinomial_result = np.random.multinomial(len(extracted_people), self.exits["distribution"])
            # multinomial_result will be something like [0,1,3]
            # this means that 0 people will go to the first exit, 1 person to the second and 3 people to the third
            for i, result in enumerate(multinomial_result):
                for person in range(0, result):
                    self.ski_lifts_queues[i].append(extracted_people.pop(0))

        for exit_idx,exit in enumerate(self.exits['slopes']):
            # take the number of people that will exit from the ski lift queue
            # equals to the min between ski lift capacity and the people in the queue
            # but if the ski lit capability is == -1 all the people in the ski lift queue
            # can be pushed on the next slope
            if self.exits['ski_lifts_capacities'][exit_idx] == -1:
                people_on_ski_lift = len(self.ski_lifts_queues[exit_idx])
            else:
                people_on_ski_lift = min(len(self.ski_lifts_queues[exit_idx]), self.exits['ski_lifts_capacities'][exit_idx])
            # pop people_on_ski_lift people from the ski lift queue and push them to the exit slope
            for p in range(0, people_on_ski_lift):
                person = self.ski_lifts_queues[exit_idx].pop(0)
                # if mqtt broker is not None, send the NFC topic to the mqtt broker
                if mqtt_broker_host is not None and self.name != 'root':
                    topic = "/NFC/{}".format(person.uuid)
                    try:
                        publish.single(topic, self.station_name, hostname=mqtt_broker_host, qos=2)
                    except:
                        print("unable to publish on the topic", topic)

                exit.push(person)

    def push(self, person):
        # insert person in the slope queue cache
        # A cache is used because in the same popping round the item in the
        # cache are not used
        self.slope_queue_cache.append({'object': person, 'timer': random.randint(self.slope_time[0], self.slope_time[1])})

    def empty_cache(self):
        for item in self.slope_queue_cache:
            self.slope_queue.append(item)
        self.slope_queue_cache = []

    def set_slope_queue(self, people):
        self.ski_lift_queue = [{'object': person, 'timer': self.slope_time} for person in people]

    def get_slope_queue(self):
        return self.slope_queue

    def get_ski_lifts_queues(self):
        result = []
        for exit_id, exit in enumerate(self.exits['slopes']):
            result.append({"slope": exit.name, "ski_lift_queue": len(self.ski_lifts_queues[exit_id])})
        return result

    def get_info(self):
        return {"name": self.name, "slope_time": self.slope_time,
                "exits": {"slopes": [slope.name for slope in self.exits["slopes"]], "distribution": self.exits["distribution"],
                          "ski_lifts_capacities": self.exits["ski_lifts_capacities"]}}
