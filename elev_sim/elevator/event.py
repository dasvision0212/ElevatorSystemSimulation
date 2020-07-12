class Event:
    def __init__(self, env, floorList, elevatorList):
        self.env = env

        self.CALL = env.event()
        self.ELEV_ARRIVAL = { 1: {i: env.event() for i in floorList},
                             -1: {i: env.event() for i in floorList}}
        self.ELEV_LEAVE = {i: env.event() for i in elevatorList}
