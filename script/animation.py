import json
import sys
from collections import defaultdict
sys.path.append('../')

from elev_sys import Animation


background = None # first initialized to catch the data read from json file below
with open("../data/log2/background.json", 'r', encoding="utf-8") as file:
    background = json.load(file)


Animation(background["buildingName"], 
          "../data/log/elev_log.csv", 
          "../data/log/queue_log.csv", 
          "../data/log/stopList_log.csv", 
          "../data/log/customer_log.csv", 
          background["elevatorList"], background["floorList"], defaultdict(list, background["elev_available_floor"]))