from elev_sys.simulation import sub_group
import simpy
import numpy as np
import pandas as pd
import scipy.stats as st
from collections import namedtuple
from copy import deepcopy
import logging
from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.simulation.simple_data_structure import Mission
from elev_sys.simulation.event import Event
from elev_sys.simulation.logger import Queue_logger, Customer_logger
from elev_sys.simulation.utils import floor_complement, floor_to_index, index_to_floor, advance_toward, floor_complement

def cid_generator():
        ''' Generate unique, global customer ID.[!] In order to maintain the feasibility of Customer_logger, cid must start from 0. '''
        i = 0
        while True:
            yield i
            i += 1

class Customer:
    def __init__(self, cid_gen=None):
        if cid_gen is not None:
            self.cid = next(cid_gen)
        else:
            self.cid = next(self._cid_generator)

        self.source = None
        self.destination = None
        self.leave_time = None

        self.temp_destination = None

    def select_destination(self, current_floor, direction, floorList, available_floor):
  
        infeasible_floor = floor_complement(floorList, available_floor)
        if str(self.destination) in infeasible_floor:
            infeasible_floor = [floor_to_index(floor) for floor in infeasible_floor]
            
            current_floor = floor_to_index(current_floor)
            if direction == 1:
                t = [floor for floor in infeasible_floor if not floor <= current_floor]
            if direction == -1:
                t = [floor for floor in infeasible_floor if not floor >= current_floor]
 
            temp_destination_index = t[min(range(len(t)), key = lambda i: abs(t[i]-current_floor))] - direction

            self.temp_destination = index_to_floor(temp_destination_index)
            return self.temp_destination
        return self.destination 

class Queue:
    def __init__(self, env, floorList, floor, floorIndex, direction, group_setting, EVENT:Event, 
                queue_logger:Queue_logger=None, customer_logger:Customer_logger=None):
        self.env = env
        self.floorList = floorList
        self.floor = floor
        self.floorIndex = floorIndex
        self.direction = direction
        self.queue_array = []
        self.arrival_event = self.env.event()

        self.group_setting = group_setting

        # start process
        self.inflow_proc = self.env.process(self.inflow())
        self.outflow_proc = self.env.process(self.outflow())

        self.EVENT = EVENT
        self.queue_logger = queue_logger
        self.customer_logger = customer_logger

    #     self.env.process(self.debug())
    # def debug(self):
    #     if True:#(self.floor == '5') & (self.direction == -1):
    #         while True:
    #             yield self.env.timeout(100)
    #             print(self.env.now,'Floor',self.floor, 'direction',self.direction, 'num:', len(self.queue_array))
                
        
    def rigisterCall(self):
        # Call registration when customer arrive
        for customer in self.queue_array:
            for sub_group_name, sub_group_setting in self.group_setting.items():

                # each elevator
                for available_floor in sub_group_setting["available_floor"]:
                    # temporary destination of customer
                    temp_destination = customer.select_destination(self.floor, self.direction, self.floorList, available_floor)

                    # if elevator can arrive current floor & if elevator serves floors between customer's destination
                    if (self.floor in available_floor) & (advance_toward(self.floor, temp_destination) in available_floor):

                        mission = Mission(direction=self.direction, destination=self.floor)

                        self.EVENT.CALL[sub_group_name].succeed(value=mission)
                        self.EVENT.CALL[sub_group_name] = self.env.event()
    
    def updatePanel(self):
        # delay call registration until elevator left
        yield self.env.timeout(ELEV_CONFIG.CUSTOMER__RECALL_ELEV_TIME)
        self.rigisterCall()

    def inflow(self):
        while True:

            # new customer | transfer customer
            customers = yield self.arrival_event | self.EVENT.ELEV_TRANSFER[self.direction][self.floor]
            customers = list(customers.values())[0] # Unpack simPy comdition variable

            logging.info('[INFLOW] Outer Call {} Floor {} '.format(
                self.floor, 'up' if self.direction == 1 else 'down'))

            # append customers to waiting queue
            self.queue_array = self.queue_array + customers

            # call registeration
            self.rigisterCall()

            logging.info('[INFLOW] {} people waiting on {} floor'.format(len(self.queue_array), self.floor))
            if(not self.queue_logger is None):
                self.queue_logger.log_inflow(len(self.queue_array), self.floorIndex, self.direction, float(self.env.now))
    
    def outflow(self):
        while True:

            # elevator arrival
            space, elev_name = yield self.EVENT.ELEV_ARRIVAL[self.direction][self.floor]

            riders = []

            index = 0
            while (space > 0) & (len(self.queue_array) > 0) & (not index == len(self.queue_array)):
                customer = self.queue_array[index]
                
                # available_floor of elevator
                sub_group_name = elev_name[0]
                elev_index     = int(elev_name[1:])
                available_floor = self.group_setting[sub_group_name]["available_floor"][elev_index]

                # temporary destination of customer
                temp_destination = customer.select_destination(self.floor, self.direction, self.floorList, available_floor)
                
                # if elevator serves floors between customer's destination
                if (advance_toward(self.floor, temp_destination) in available_floor):
                    riders.append(customer)
                    self.queue_array.pop(index)
                    space -= 1
                    
                    # micmic customer enter time
                    yield self.env.timeout(np.random.randint(ELEV_CONFIG.WALKING_MIN, ELEV_CONFIG.WALKING_MAX))
                        
                    if(not self.customer_logger is None):
                        self.customer_logger.log_board(customer.cid, float(self.env.now))
                else:
                    index += 1
            
            logging.info('[OUTFLOW] {} People Enters'.format(len(riders)))
            if(not self.queue_logger is None):
                self.queue_logger.log_outflow(len(self.queue_array), self.floorIndex, self.direction, float(self.env.now))

            # customers on board
            self.EVENT.ELEV_LEAVE[elev_name].succeed(value=riders)
            self.EVENT.ELEV_LEAVE[elev_name] = self.env.event()

            # Call registration after elevator left
            self.env.process(self.updatePanel())

class Floor:
    def __init__(self, env, floorList, floor, floorIndex, direction, IAT, distination_dist, group_setting, cid_gen, EVENT:Event, 
                 queue_logger:Queue_logger=None,
                 customer_logger:Customer_logger=None):
        self.env = env
        self.floor = floor
        self.direction = direction
        self.floorList = floorList

        # customer behaviors data
        self.IAT = IAT
        self.distination_dist = distination_dist if len(distination_dist) == 1 else distination_dist/distination_dist.sum()

        # start process
        self.queue = Queue(env, floorList, floor, floorIndex, direction, group_setting, EVENT, 
                            queue_logger=queue_logger, customer_logger=customer_logger)
        self.source_proc = env.process(self.Source(env))

        # global
        self.cid_gen = cid_gen
        self.customer_logger = customer_logger

    def Source(self, env):
        while True:
            # 1. inter-arrival time based on given distribution
            t = -1
            while t < 0:
                t = self.IAT['dist'].rvs(
                    *self.IAT['params'][:-2], loc=self.IAT['params'][-2], scale=self.IAT['params'][-1], size=1)
            yield self.env.timeout(t)

            # 2. number of people of arrival group
            number_of_arrival = np.random.randint(ELEV_CONFIG.ARRIVAL_MIN, ELEV_CONFIG.ARRIVAL_MAX)


            customers = []
            for i in range(number_of_arrival):
                
                # 3. customer destination based on given posibility
                customer = Customer(self.cid_gen)
                customer.destination = np.random.choice(self.distination_dist.index, p=self.distination_dist)

                if(not self.customer_logger is None):
                    self.customer_logger.log_appear(customer.cid, self.floor, customer.destination, float(self.env.now))

                # 4. redirect to other elevator group

                customers.append(customer)

            self.queue.arrival_event.succeed(value=customers)
            self.queue.arrival_event = self.env.event()
