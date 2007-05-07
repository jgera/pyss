#!/usr/bin/env python2.4

from sim import * 
 

class Event:
    def __init__(self, job=None):
        self.job = job

class JobArrivalEvent(Event):
    def __str__(self):
        return "Job Arrival Event: " + str(self.job)

class JobTerminationEvent(Event):
     def __str__(self):
        return "Job Termination Event: " + str(self.job)

class EndOfSimulationEvent(Event):
    def __str__(self):
        return "End of Simulation Event" 



class Events:
    
    def __init__(self):
        self.collection = {}
        self.endOfSimulationFlag = False

    def _addEvent(self, time, event): 
         if self.collection.has_key(time):
             self.collection[time].append(event)
         else:
             self.collection[time] = []
             self.collection[time].append(event)


    def add_job_arrival_event(self, time, job): # adds a single arrival event to the collection
        event = JobArrivalEvent(job)
        self._addEvent(time, event)
        
    def add_job_termination_event(self, time, job):
        # makes sure that there will be a single termination event for this job
        # assert time >= 0
        event = JobTerminationEvent(job)
        self._addEvent(time, event)


    def add_end_of_simulation_event(self, time):
        # makes sure that there will be a single end of simulation event
        # assert time >= 0
        if self.endOfSimulationFlag == False:
            event = EndOfSimulationEvent()
            self._addEvent(time, event)     
            self.endOfSimulationFlag = True
            return 	
         
        found = False
        for t, list_of_events_at_this_time in self.collection.iteritems():
            if found:
                break 
            for event in self.collection[t]:
                if isinstance(event, EndOfSimulationEvent):
                    list_of_events_at_this_time.remove(event)
                    found = True
                    break
        event = EndOfSimulationEvent()
        self._addEvent(time, event)     
   

    def addEvents(self, new_events): # combines a new collection of events with the self collection        
         for time, new_list_of_events_at_this_time in new_events.collection.iteritems():
             for new_event in new_list_of_events_at_this_time:         
                 if isinstance(new_event, JobTerminationEvent):
                     self.add_job_termination_event(time, new_event.job)
                 elif isinstance(new_event, JobArrivalEvent): 
                     self.add_job_arrival_event(time, new_event.job)                     
                 else:
                     self.add_end_of_simulation_event(time)



    def printEvents(self): # SHOULD IT BE __STR__????
        times = self.collection.keys()
        times.sort()
        for t in times:
            for event in self.collection[t]: 
                print event 
        print
         