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
from elev_sys.simulation.logger import Queue_logger


def cid_generator():
        '''Generate unique, global customer ID.'''
        i = 1
        while True:
            yield i
            i += 1


class Customer:

    @staticmethod
    def _cid_generator(self):
        '''Generate unique, global customer ID.'''
        i = 1
        while True:
            yield i
            i += 1

    def __init__(self, cid_gen=None):
        if(cid_gen != None):
            self.cid = next(cid_gen)
        else:
            self.cid = next(self._cid_generator)
        self.source = None
        self.destination = None
        self.start_time = None
        self.boarding_time = None
        self.leave_time = None


class Queue:
    def __init__(self, env, floor, floorIndex, direction, sub_group_setting, EVENT:Event, queue_logger:Queue_logger=None):
        self.env = env
        self.floor = floor
        self.floorIndex = floorIndex
        self.direction = direction
        self.queue_array = []
        self.arrival_event = self.env.event()

        # !!subgroup
        self.panels = dict(zip(sub_group_setting, [False]*len(sub_group_setting)))
        self.sub_group_setting = sub_group_setting

        # start process
        self.inflow_proc = self.env.process(self.inflow())
        self.outflow_proc = self.env.process(self.outflow())

        self.EVENT = EVENT
        self.queue_logger = queue_logger

    def inflow(self):
        while True:
            customers = yield self.arrival_event
            
            logging.info('[INFLOW] Outer Call {} Floor {} '.format(
                self.floor, 'up' if self.direction == 1 else 'down'))

            # disable call if already assigned
            for customer in customers:
                for sub_group_name in self.sub_group_setting.keys():
                    if customer.destination not in self.sub_group_setting[sub_group_name]['infeasible']:
                        if self.panels[sub_group_name] == False:
                            self.panels[sub_group_name] == True
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
            sub_group_name = elevIndex[0]
            self.panels[sub_group_name] = False

            riders = []

            customerIndex = 0
            while (availible > 0) and (len(self.queue_array) > 0):
                customer = self.queue_array[customerIndex]

                if(customer.destination not in ELEV_INFEASIBLE[elevIndex]):
                    customer.boarding_time = float(self.env.now)
                    riders.append(customer)
                    self.queue_array.pop(customerIndex)
                    availible -= 1
                else:
                    customerIndex += 1

            # time the customers take to on board
            yield self.env.timeout(len(riders) * random.randint(ELEV_CONFIG.WALKING_MIN, ELEV_CONFIG.WALKING_MAX))
            logging.info('[OUTFLOW] {} People Enters'.format(len(riders)))
            
            if(self.queue_logger != None):
                self.queue_logger.log_outflow(len(self.queue_array), self.floorIndex, self.direction, float(self.env.now))

            # customers on board
            self.EVENT.ELEV_LEAVE[elevIndex].succeed(value=riders)
            self.EVENT.ELEV_LEAVE[elevIndex] = self.env.event()

class Floor:
    def __init__(self, env, floor, floorIndex, direction, IAT, distination_dist, sub_group_setting, cid_gen, EVENT:Event, queue_logger:Queue_logger=None):
        self.env = env
        self.floor = floor
        self.direction = direction

        # statistical data
        self.IAT = IAT
        self.distination_dist = distination_dist if len(distination_dist) == 1 else distination_dist/distination_dist.sum()

        # start process
        self.queue = Queue(env, self.floor, floorIndex, self.direction, sub_group_setting, EVENT, queue_logger=queue_logger)
        self.source_proc = env.process(self.Source(env))
        
        # global
        self.cid_gen = cid_gen

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
                customer.source = self.floor
                customer.destination = random.choice(self.distination_dist.index, p=self.distination_dist)
                customer.start_time = float(self.env.now)

                customers.append(customer)

            self.queue.arrival_event.succeed(value=customers)
            self.queue.arrival_event = self.env.event()
