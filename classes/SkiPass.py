class SkiPass:

    def __init__(self, uuid, battery=100):
        self.uuid = uuid
        self.battery = battery

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_battery(self, battery):
        self.battery = battery

    def get_uuid(self):
        return self.uuid

    def get_battery(self):
        return self.battery