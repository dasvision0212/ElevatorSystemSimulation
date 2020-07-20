import sys
sys.path.append('../')

from elev_sim import Animation

building_name = "北棟客梯"
floorList = ['B4','B3','B1','1','2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
# Elevator ID
elevatorList = ['3001', "3002", "3003", "3004", "3005"]

Animation(building_name, "../data/elevator_log.csv", "../data/queue_log.csv", elevatorList, floorList)