import random

import numpy as np


class Slope:
    def __init__(self, name, station_name=None, slope_time=(1,5), ski_lift_capacity=1):
        self.name = name
        if station_name == None:
            self.station_name = name
        else:
            self.station_name = station_name
        self.slope_queue_cache = []
        self.slope_queue = []
        self.ski_lift_queue = []
        self.slope_time = slope_time
        self.exits = {}
        self.ski_lift_capacity = ski_lift_capacity

    def set_exits(self, exits):
        self.exits = exits

    def pop(self):
        # insert people with timer == 0 into ski_lift_queue
        self.ski_lift_queue = self.ski_lift_queue + [x['object'] for x in self.slope_queue if x['timer'] == 0]
        # recreate slope queue without people with timer == 0
        self.slope_queue = [x for x in self.slope_queue if x['timer'] != 0]

        # reduce timer of each person in the slope queue
        for item in self.slope_queue:
            item['timer'] -= 1

        # exit people ski_lift_capacity people from the lift queue
        # if the pop fails (no people in the lift queue) just break the loop
        exiting_people = []
        if self.ski_lift_capacity == -1:
            exiting_people = self.ski_lift_queue
        else:
            for n in range(0, self.ski_lift_capacity):
                try:
                    exiting_people.append(self.ski_lift_queue.pop(0))
                except:
                    break

        if len(exiting_people) > 0:
            # extract len(exiting_people) number from a multinomial distribution
            # define on the probability distribution for the slope's exits configuration
            multinomial_result = np.random.multinomial(len(exiting_people), self.exits["distribution"])
            # multinomial_result will be something like [0,1,2]
            # this means that 0 people will go to the first exit, 1 person to the second and 2 people to the third
            for i, result in enumerate(multinomial_result):
                for person in range(0, result):
                    self.exits['slopes'][i].push(exiting_people.pop(0))


    def push(self, person):
        # insert person in the slope queue cache
        # A cache is used because in the same popping round the item in the
        # cache are not used
        self.slope_queue_cache.append({'object': person, 'timer': random.randint(self.slope_time[0], self.slope_time[1])})

    def empty_cache(self):
        for item in self.slope_queue_cache:
            self.slope_queue.append(item)
        self.slope_queue_cache = []

    def set_ski_lift_queue(self, people):
        self.ski_lift_queue = people

    def set_slope_queue(self, people):
        self.ski_lift_queue = [{'object': person, 'timer': self.slope_time} for person in people]

    def get_slope_queue(self):
        return self.slope_queue

    def get_ski_lift_queue(self):
        return self.ski_lift_queue

    def get_info(self):
        return {"name": self.name, "slope_time": self.slope_time, "ski_lift_capacity": self.ski_lift_capacity,
                "exits": {"slopes": [slope.name for slope in self.exits["slopes"]], "distribution": self.exits["distribution"]}}
