
class Slope:
    def __init__(self, name, slope_time = 5):
        self.name = name
        self.slope_queue_cache = []
        self.slope_queue = []
        self.ski_lift_queue = []
        self.slope_time = slope_time
        self.exits = {}
        self.ski_lift_capacity = None

    def set_exits(self, exits):
        self.exits = exits
        self.ski_lift_capacity = 0
        for exit in exits:
            self.ski_lift_capacity += exit['distribution']

    def pop(self):
        #insert people with timer == 0 into ski_lift_queue
        self.ski_lift_queue  = self.ski_lift_queue + [x['object'] for x in self.slope_queue if x['timer'] == 0]
        #recreate slope queue without people with timer == 0
        self.slope_queue = [x for x in self.slope_queue if x['timer'] != 0]

        # reduce timer of each person in the slope queue
        for item in self.slope_queue:
            item['timer'] -= 1

        exiting_people = []
        for n in range(0, self.ski_lift_capacity):
            try:
                exiting_people.append(self.ski_lift_queue.pop(0))
            except:
                break


        if len(exiting_people)>0:
            #for each exit in exits
            for exit in self.exits:
                #pop n element from the exiting_list and push them into the right slope
                for n in range(0, exit['distribution']):
                    if len(exiting_people) > 0:
                        exiting_person = exiting_people.pop(0)
                        exit['object'].push(exiting_person)

    def push(self, person):
        #insert person in the slope queue cache
        # A cache is used because in the same popping round the item in the
        # cache are not used
        self.slope_queue_cache.append({'object': person, 'timer': self.slope_time})

    def empty_cache(self):
        for item in self.slope_queue_cache:
            self.slope_queue.append(item)
        self.slope_queue_cache = []

    def set_ski_lift_queue(self, people):
        self.ski_lift_queue = people

    def set_slope_queue(self, people):
        self.ski_lift_queue = [{'object':person, 'timer':self.slope_time} for person in people]

    def get_slope_queue(self):
        return self.slope_queue

    def get_ski_lift_queue(self):
        return self.ski_lift_queue