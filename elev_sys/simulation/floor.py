import simpy
import numpy.random as random
import pandas as pd
import scipy.stats as st
from collections import namedtuple
from copy import deepcopy
import logging

from elev_sys.conf.NTUH_conf import ELEV_INFEASIBLE
from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.simulation.simple_data_structure import Mission
from elev_sys.simulation.event import Event
from elev_sys.simulation.logger import Queue_logger, Customer_logger


def cid_generator():
        '''
        Generate unique, global customer ID.
        [!] In order to maintain the feasibility of Customer_logger, cid must start from 0.
        '''
        
        i = 0
        while True:
            yield i
            i += 1


class Customer:
    def __init__(self, cid_gen=None):
        if(cid_gen != None):
            self.cid = next(cid_gen)
        else:
            self.cid = next(self._cid_generator)
        self.source = None
        self.destination = None
        self.leave_time = None

        self.temp_destination = None

    def select_destination(self, current_floor, direction, infeasible):
        # need tranfer

        if str(self.destination) in infeasible:
            infeasible = [int(floor) if not 'B' in floor else -int(floor[1:]) + 1 for floor in infeasible]
            current_floor = int(current_floor) if not 'B' in current_floor else -int(current_floor[1:]) + 1
            if direction == 1:
                t = [floor for floor in infeasible if not floor < current_floor]
            if direction == -1:
                t = [floor for floor in infeasible if not floor > current_floor]
            temp_destination_index = t[min(range(len(t)), key = lambda i: abs(t[i]-current_floor))] - direction
            self.temp_destination = str(temp_destination_index) if temp_destination_index > 0  else 'B'+str(-(temp_destination_index-1))
            return self.temp_destination
        return self.destination 

class Queue:
    def __init__(self, env, floor, floorIndex, direction, group_setting, EVENT:Event, 
                queue_logger:Queue_logger=None, customer_logger:Customer_logger=None):
        self.env = env
        self.floor = floor
        self.floorIndex = floorIndex
        self.direction = direction
        self.queue_array = []
        self.arrival_event = self.env.event()

        # !!subgroup
        self.panels_state = dict(zip(group_setting, [False]*len(group_setting)))
        self.group_setting = group_setting

        # start process
        self.inflow_proc = self.env.process(self.inflow())
        self.outflow_proc = self.env.process(self.outflow())

        self.EVENT = EVENT
        self.queue_logger = queue_logger
        self.customer_logger = customer_logger

    def inflow(self):
        while True:
            customers = yield self.arrival_event or self.EVENT.ELEV_TRANSFER
            logging.info('[INFLOW] Outer Call {} Floor {} '.format(
                self.floor, 'up' if self.direction == 1 else 'down'))

            # fo each customer
            for customer in customers:
                # for each sub-group
                for sub_group_name, sub_group_setting in self.group_setting.items():

                    # for each elevator
                    for infeasible in sub_group_setting['infeasibles']:

                        # if served by current elevator
                        if self.floor not in infeasible:

                            # disable call if already assigned
                            if self.panels_state[sub_group_name] == False:
                                self.panels_state[sub_group_name] == True
                                mission = Mission(direction=self.direction, destination=self.floor)
                                self.EVENT.CALL[sub_group_name].succeed(value=mission)
                                
                                # reactivate event
                                self.EVENT.CALL[sub_group_name] = self.env.event()

            # if(len(self.queue_array) == 0):
            #     mission = Mission(direction=self.direction,
            #                       destination=self.floor)
            #     self.EVENT.CALL.succeed(value=mission)

            #     # reactivate event
            #     self.EVENT.CALL = self.env.event()

            # add customers to waiting queue
            self.queue_array = self.queue_array + customers
            logging.info('[INFLOW] {} people waiting on {} floor'.format(
                len(self.queue_array), self.floor))

            if(self.queue_logger != None):
                self.queue_logger.log_inflow(len(self.queue_array), self.floorIndex, self.direction, float(self.env.now))

    def outflow(self):
        while True:
            # elevator arrives
            availible, elevIndex = yield self.EVENT.ELEV_ARRIVAL[self.direction][self.floor]

            # cancel panel
            self.panels_state[elevIndex[0]] = False

            riders = []

            customerIndex = 0
            while (availible > 0) and (len(self.queue_array) > 0):
                customer = self.queue_array[customerIndex]

                if(customer.destination not in ELEV_INFEASIBLE[elevIndex]):
                    if(self.customer_logger != None):
                        yield self.env.timeout(random.randint(ELEV_CONFIG.WALKING_MIN, ELEV_CONFIG.WALKING_MAX))
                        self.customer_logger.log_board(customer.cid, float(self.env.now))
                    
                    riders.append(customer)
                    self.queue_array.pop(customerIndex)
                    availible -= 1
                else:
                    customerIndex += 1
            
            logging.info('[OUTFLOW] {} People Enters'.format(len(riders)))
            
            if(self.queue_logger != None):
                self.queue_logger.log_outflow(len(self.queue_array), self.floorIndex, self.direction, float(self.env.now))

            # customers on board
            self.EVENT.ELEV_LEAVE[elevIndex].succeed(value=riders)
            self.EVENT.ELEV_LEAVE[elevIndex] = self.env.event()

class Floor:
    def __init__(self, env, floor, floorIndex, direction, IAT, distination_dist, group_setting, cid_gen, EVENT:Event, 
                 queue_logger:Queue_logger=None, customer_logger:Customer_logger=None):
        self.env = env
        self.floor = floor
        self.direction = direction

        # statistical data
        self.IAT = IAT
        self.distination_dist = distination_dist if len(distination_dist) == 1 else distination_dist/distination_dist.sum()

        # start process
        self.queue = Queue(env, floor, floorIndex, direction, group_setting, EVENT, 
                            queue_logger=queue_logger, customer_logger=customer_logger)
        self.source_proc = env.process(self.Source(env))

        # global
        self.cid_gen = cid_gen
        self.customer_logger = customer_logger

    def Source(self, env):
        while True:
            # 1. set inter-arrival time based on given distribution
            t = -1
            while t < 0:
                t = self.IAT['dist'].rvs(
                    *self.IAT['params'][:-2], loc=self.IAT['params'][-2], scale=self.IAT['params'][-1], size=1)
            yield self.env.timeout(t)

            # 2. set number of people of arrival group
            customers = []
            for i in range(random.randint(ELEV_CONFIG.ARRIVAL_MIN, ELEV_CONFIG.ARRIVAL_MAX)):
                # 3. set customer destination based on given posibility
                customer = Customer(self.cid_gen)
                customer.destination = random.choice(self.distination_dist.index, p=self.distination_dist)

                if(self.customer_logger != None):
                    self.customer_logger.log_appear(customer.cid, self.floor, customer.destination, float(self.env.now))

                customers.append(customer)

            self.queue.arrival_event.succeed(value=customers)
            self.queue.arrival_event = self.env.event()
