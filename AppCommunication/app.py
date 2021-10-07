import json
class App:
    def __init__(self, deviceID, ip, port, package, intentLauncher, ready):
        self.deviceID = deviceID
        self.ip = ip
        self.port = port
        self.package = package
        self.intentLauncher = intentLauncher
        self.ready = ready

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=1)


    def asString(self):
        return "deviceID: %s \n" \
               "ip: %s \n" \
               "port: %s \n" \
               "package: %s \n" \
               "intentLauncher: %s \n" \
               "ready: %r" % (self.deviceID, self.ip, self.port, self.package, self.intentLauncher, self.ready)


    def asHTML(self):
        return "<b>deviceID: %s</b> <br>" \
               "ip: %s <br>" \
               "port: %i <br>" \
               "package: %s <br>" \
               "intentLauncher: %s <br>" \
               "ready: %r" % (self.deviceID, self.ip, self.port, self.package, self.intentLauncher, self.ready)