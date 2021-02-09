from sys import path
from elev_sys.simulation import sub_group
import simpy
import numpy as np
import random
import pandas as pd
import scipy.stats as st
from collections import namedtuple, defaultdict
from copy import deepcopy
import logging
import itertools
from elev_sys.conf.elevator_conf import ELEV_CONFIG
from elev_sys.simulation.event import Event
from elev_sys.simulation.logger import Queue_logger, Customer_logger
from elev_sys.simulation.utils import floor_complement, floor_to_index, index_to_floor, floor_complement, compare_direction, Mission
from elev_sys.simulation.path_finder import Path_finder



def cid_generator():
    ''' Generate unique, global customer ID.[!] In order to maintain the feasibility of Customer_logger, cid must start from 0. '''
    i = 0
    while True:
        yield i
        i += 1


class Customer:
    def __init__(self, floor, path_finder:Path_finder, cid_gen=None, ):
        if cid_gen is not None:
            self.cid = next(cid_gen)
        else:
            self.cid = next(self._cid_generator)

        self.source = floor
        self.destination = None
        self.leave_time = None

        self.path = None
        self._current_stop_i = 0
    @property
    def next_stop(self):
        return self.path[self._current_stop_i + 1]

    def select_tour(self, destination_dist, path_finder):
        self.destination = np.random.choice(destination_dist.index, p=destination_dist)
        path_candidate = path_finder.map[self.source][self.destination]
        # decision = 0
        # if(len(path_candidate) > 1): 
        #     decision = np.random.randint(0, len(path_candidate)-1)
        # self.path = path_candidate[decision]
        self.path = random.choice(path_candidate)

    def enterQueue(self):
        self._current_stop_i = self._current_stop_i + 1


class Queue:
    def __init__(self, env, floorList, floor, floorIndex, direction, group_setting, EVENT:Event, path_finder:Path_finder, 
                queue_logger:Queue_logger=None, customer_logger:Customer_logger=None):
        self.env = env
        self.floorList = floorList
        self.floor = floor
        self.floorIndex = floorIndex
        self.direction = direction
        self.queue_array = []
        self.arrival_event = self.env.event()
        self.group_setting = group_setting
        self.path_finder = path_finder

        self.buttonPushed = {sub_group_name: False for sub_group_name in self.group_setting.keys()}
        
        # start process
        self.inflow_proc = self.env.process(self.inflow())
        self.outflow_proc = self.env.process(self.outflow())

        self.EVENT = EVENT
        self.queue_logger = queue_logger
        self.customer_logger = customer_logger

    #     self.env.process(self.debug())
    # def debug(self):
    #     if (self.floor == '9') & (self.direction == -1):
    #         while True:
    #             yield self.env.timeout(100)
    #             print(self.env.now,'Floor',self.floor, 'direction',self.direction, 'num:', len(self.queue_array))
                


    def rigisterCall(self):
        # Call registration when customer arrive

        for sub_group_name, sub_group_setting in self.group_setting.items():

            if not self.buttonPushed[sub_group_name]:

                for customer in self.queue_array:
                    for available_floor in sub_group_setting["available_floor"]:

                        if customer.next_stop in available_floor:
                            mission = Mission(direction=self.direction, destination=self.floor)
                            self.EVENT.CALL[sub_group_name].succeed(value=mission)
                            self.EVENT.CALL[sub_group_name] = self.env.event()
                            if (self.floor == '1') and (self.direction == 1):
                                print(self.env.now, 'CALL')
                            self.buttonPushed[sub_group_name] = True
                            break
                    
                    if self.buttonPushed[sub_group_name]:
                        break

    def inflow(self):
        while True:

            # new customer | transfer customer
            customers = yield self.arrival_event | self.EVENT.ELEV_TRANSFER[self.direction][self.floor]
            customers = list(customers.values())[0] # Unpack simPy comdition variable

            # if (self.floor == '1') and (self.direction == 1):
            #     print('number',len(customers))
            logging.info('[INFLOW] Outer Call {} Floor {} '.format(
                self.floor, 'up' if self.direction == 1 else 'down'))

            
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
            if (self.floor == '1') and (self.direction == 1):
                print(self.env.now, 'outflow')
            riders = []

            # available_floor of elevator
            sub_group_name = elev_name[0]
            self.buttonPushed[sub_group_name] = False

            elev_index     = int(elev_name[1:])

            available_floor = self.group_setting[sub_group_name]["available_floor"][elev_index]

            index = 0
            while (space > 0) and (len(self.queue_array) > 0) and (not index == len(self.queue_array)):
                
                customer = self.queue_array[index]

                # if elevator serves floors between customer's destination
                if customer.next_stop in available_floor:
                    riders.append(customer)
                    self.queue_array.pop(index)
                    space -= 1
                    
                    # simulate customer enter time
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
            self.rigisterCall()


class Floor:
    def __init__(self, env, floorList, floor, floorIndex, IAT_df, destination_dist, group_setting, cid_gen, EVENT:Event, path_finder:Path_finder, 
                 queue_logger:Queue_logger=None,
                 customer_logger:Customer_logger=None):
        self.env = env
        self.floor = floor
        self.floorList = floorList
        self.group_setting = group_setting
        self.path_finder = path_finder

        # customer behaviors data
        self.IAT = {}
        self.source_proc = {}
        self.queue = {}
        self.destination_dist = {}

        for direction in [-1, 1]:
            IAT = IAT_df.getter(direction, floor)
            if IAT:
                self.IAT[direction] = IAT
                self.source_proc[direction] = env.process(self.Source(env, direction))
                if direction == 1:
                    self.destination_dist[direction] = destination_dist[floorIndex+1:]/destination_dist[floorIndex+1:].sum()
                elif direction == -1:
                    self.destination_dist[direction] = destination_dist[:floorIndex]/destination_dist[:floorIndex].sum()
            


            self.queue[direction] = Queue(env, floorList, floor, floorIndex, direction, group_setting, EVENT, path_finder, 
                            queue_logger=queue_logger, customer_logger=customer_logger)

        # global
        self.cid_gen = cid_gen
        self.customer_logger = customer_logger


    def Source(self, env, direction):
        while True:
            # 1. inter-arrival time based on given distribution
            t = -1
            while t < 0:
                t = self.IAT[direction]['dist'].rvs(
                    *self.IAT[direction]['params'][:-2], loc=self.IAT[direction]['params'][-2], scale=self.IAT[direction]['params'][-1], size=1)
            yield self.env.timeout(t)

            # 2. number of people of arrival group
            number_of_arrival = np.random.randint(ELEV_CONFIG.ARRIVAL_MIN, ELEV_CONFIG.ARRIVAL_MAX)

            customers = defaultdict(list)
            for i in range(number_of_arrival):
                
                # 3. customer destination based on given posibility
                customer = Customer(self.floor, self.path_finder, self.cid_gen)
                customer.select_tour(self.destination_dist[direction], self.path_finder)

                if(not self.customer_logger is None):
                    self.customer_logger.log_appear(customer.cid, self.floor, customer.destination, float(self.env.now))

                # 4. redirect to other elevator group

                next_direction = compare_direction(self.floor, customer.next_stop)
                customers[next_direction].append(customer)

                # if self.floor == '1':
                #     print(self.floor, customer.destination,  customer.next_stop, next_direction)
                
            for di in [-1, 1]:
                self.queue[di].arrival_event.succeed(value=customers[di])
                self.queue[di].arrival_event = self.env.event()
