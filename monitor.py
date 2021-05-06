import os.path
import random
import re
import sys
import threading

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from paho.mqtt.client import Client

from exceptions import NoBackgroundImage


def update_monitor(window, stations):
    client = Client(client_id="monitor_{}".format(random.randint(0,9999)))
    print("Thread started, client {}".format(client))

    def on_connect(client, userdata, flags, rc):
        print("Connected!")
        if rc == 0:
            client.connected_flag = True  # set flag
            print("connected OK Returned code=%s", rc)
        else:
            print("Bad connection Returned code=%s", rc)

    def on_message(client, userdata, message):
        print ("message received on topic {}".format(message.topic))
        print ("Payload: {}".format(message.payload.decode()))

        pattern = "/station(.*?)/totalPeople"
        station_id = re.search(pattern, message.topic).group(1)

        if station_id in stations:
            print ("station {} in stations, updating display..")
            message_payload = message.payload.decode()
            label = window.findChildren(QLabel, name=("label_" + station_id))
            label[0].setText("station{}: {}".format(station_id, message_payload))
            label[0].adjustSize()

    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting")
    client.connect("192.168.1.150")
    qos = 2
    client.subscribe([
        ("/+/totalPeople", qos)
    ])

    client.loop_forever()

if __name__ == '__main__':
    #config
    background_image="monitor.png"
    stations = [s for s in sys.argv[1:]]
    print ("stations requested: ", stations)

    app = QApplication(sys.argv)

    # window and settings
    window = QWidget()
    window.setWindowTitle("Safe Skiing Monitor")
    # window position and dimension
    window.setGeometry(50, 50, 512, 512)
    # check if the background image was specified in the config
    if not os.path.isfile(background_image):
        raise NoBackgroundImage
    # set the background image
    window.setStyleSheet(
        "background-image: url(" + background_image + "); background-repeat: no-repeat; background-position: center;")

    main_window = QWidget(parent=window)
    main_window.setGeometry(45, 85, 300, 200)
    main_window.setAutoFillBackground(True);

    layout = QVBoxLayout()

    for station in stations:
        label = QLabel()
        label.setFont(QFont('Arial', 20, QFont.Bold))
        label.setStyleSheet("color: #ff0000; background: rgba(0,0,0,0);")
        label.setAutoFillBackground(True);
        label.setObjectName("label_{}".format(station))
        layout.addWidget(label)


    main_window.setLayout(layout)
    window.show()

    update_monitor_thread = threading.Thread(target=update_monitor, args=(window, stations,))
    update_monitor_thread.start()

    sys.exit(app.exec())