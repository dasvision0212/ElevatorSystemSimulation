testConfig = {
    "A":{
        "active":["B4", "B3", "B2", "B1", "1", "2", "3", "4", "5", ], 
        "elevNum": 2
    }, 
    "B":{
        "active":["1", "7", "8", "9", "10", "11", "12", "13", "14", "15"], 
        "elevNum": 2
    }, 
    "C":{
        "active":["1", "15"], 
        "elevNum": 2
    }
}


class Event:
    def __init__(self, env, floorList, elevNameList):
        self.env = env

        self.CALL = env.event()
        self.ELEV_ARRIVAL = { 1: {i: env.event() for i in floorList},
                             -1: {i: env.event() for i in floorList}}
        self.ELEV_LEAVE = {i: env.event() for i in elevNameList}
