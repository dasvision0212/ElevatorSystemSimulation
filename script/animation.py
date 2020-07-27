import json
import sys
from collections import defaultdict
sys.path.append('../')

from elev_sim import Animation, ELEV_INFEASIBLE


background = None # first initialized to catch the data read from json file below
with open("../data/log/background.json", 'r', encoding="utf-8") as file:
    background = json.load(file)

background["elev_infeasible"] = defaultdict(list, background["elev_infeasible"])
background["elev_infeasible"]["3006"] += ['1', "3"]
Animation(background["buildingName"], 
          "../data/log/elev_log.csv", 
          "../data/log/queue_log.csv", 
          "../data/log/stopList_log.csv", 
          "../data/log/customer_log.csv", 
          background["elevatorList"], background["floorList"], defaultdict(list, background["elev_infeasible"]))