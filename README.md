
# safeSkiing-simulator
Simple simulator intended to test the Safe skiing implementation.
The configuration is provided through a JSON file.

# Implementation
The simulator is implemented in Python3. It could executed wih a simple GUI that helps to understand better what is going on. 
The GUI is implemented using PyQT5.

The underlying idea for the implementation is very simple.

When a person enter in a slope the person is inserted in a queue (slope queue) and a random timer (min, max specified in the config) is assigned to him. The timer indicates the time that will take the person to travel along the slope. 
At every step the slope queue is analyzed and people with timer = 0 are extracted.
Based on the multinomial distribution indicated in the configuration people extracted from the slope queue are divided into the exits of that specific slope.
There is a queue (ski lift queue) for each exit. An exit could be a real ski lift or another slope. In the second case, the ski lift capacity need to be
set to -1 in the configuration.

**One only ski lift exit is admited for each slope.** (Only one ski lift capability for each slope will be greater than 0)

Once people that exit from the slope queue are inserted in the appropriate ski lift queue, for each queue a number of people that is identifed by the minimum between people on the queue and ski lift capacity are extracted form that queue and inserted in the next slope (the one to which the ski lift takes).

In the case in which the exit is another slope, the entire ski lift queue is emptied in the next slope.

The ski lift queues are FIFO queues.

