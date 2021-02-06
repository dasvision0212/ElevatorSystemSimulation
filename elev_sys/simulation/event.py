class Event:
    def __init__(self, env, floorList, group_setting):

        sub_group_names = group_setting.keys()
        elevNameList = []
        for sub_group_name, sub_group_setting in group_setting.items():
            for i in range(len(sub_group_setting["available_floor"])):
                elevNameList.append(sub_group_name + str(i))

        self.env = env

        self.CALL = {name :env.event() for name in sub_group_names}
        self.ELEV_ARRIVAL = { 1: {i: env.event() for i in floorList},
                             -1: {i: env.event() for i in floorList}}
        self.ELEV_TRANSFER = { 1: {i: env.event() for i in floorList},
                             -1: {i: env.event() for i in floorList}}
        self.ELEV_LEAVE = {i: env.event() for i in elevNameList}
