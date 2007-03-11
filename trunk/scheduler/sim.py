

class Job:

    def __init__(self, job_id, job_duration, job_nodes, \
                 job_arrival_time=0, job_actual_duration=0):

        assert job_nodes > 0
        self.id = job_id
        self.duration = job_duration
        self.nodes = job_nodes
        self.arrival_time = job_arrival_time
        self.start_to_run_at_time = 0 
        self.actual_duration = job_actual_duration
        

    def __str__(self):
        return str(self.id) + ", arrival " + str(self.arrival_time) + \
               ", dur " + str(self.duration) + ", #nodes " + str(self.nodes) + \
               ", startTime " + str(self.start_to_run_at_time)  
    
        

class CpuTimeSlice:
    ''' represents a "tenatative feasible" snapshot of the cpu between the start_time until start_time + dur_time.
        It is tentative since a job might be rescheduled to an earlier slice. It is feasible since the total demand
        for nodes ba all the jobs assigned to this slice never exceeds the amount of the total nodes available '''
    
    total_nodes = 0 # a class variable
    
    def __init__(self, start_time=0, duration=0, jobs={}):
        self.start_time = start_time
        self.duration = duration

        if len(jobs)==0:  
            self.free_nodes = CpuTimeSlice.total_nodes
            self.jobs = {}
           
        else:
            num_of_active_nodes = 0
            for job_id, job_nodes in jobs.iteritems(): num_of_active_nodes += job_nodes
            self.free_nodes = CpuTimeSlice.total_nodes - num_of_active_nodes 
            self.jobs = jobs.copy()               
           
            
    def __str__(self):
        return '%d %d %d %s' % (self.start_time, self.duration, self.free_nodes, str(self.jobs))
                    
            
    def addJob(self, job):
        self.free_nodes = self.free_nodes - job.nodes
        self.jobs[job.id]= job.nodes


    def delJob(self, job):
        self.free_nodes = self.free_nodes + job.nodes
        del self.jobs[job.id]

    def isMemeber(self, job):
        if job.id in self.jobs.keys():
            return True
        else: 
            return False

    def getJobs(self):
        return self.jobs.copy() 
    
    def getDuration(self):
        return self.duration

    def getFreeNodes(self):
        return self.free_nodes
    

        
        
class CpuSnapshot:
    """ represents the time table with the assignments of jobs to available nodes. """    
    def __init__(self, total_nodes=100):
        CpuTimeSlice.total_nodes = total_nodes
        self.total_nodes = total_nodes
        self.slices={} # initializing the main structure of this class 
        self.slices[0] = CpuTimeSlice() # the snapshot starts at time zero
        
            
    def addNewJobToNewSlice(self, time, duration, job):
        pass
         
    def printCpuSlices(self): 
        pass
   
    def jobEarliestAssignment(self, job, start_time=0):
        """ returns the earliest time right after the given start_time for which the job can be assigned
        enough nodes for job.duration unit of times in an uninterrupted fashion.
        Assumption: number of requested nodes is not greater than number of total nodes. """
        
        if len(self.slices) == 0: # no current job assignments, all nodes are free 
            return start_time

        partially_assigned = False
         
        times = self.slices.keys() #*** I couldn't do the sorting nicely as Ori suggested 
        times.sort()
        
        tentative_start_time = 0 
        accumulated_duration = 0
        last = 0 #just to memorize the beginning time of the last exisiting slice 
        
        for t in times: # continuity assumption: if t' is the successor of t, then: t' = t + duration_of_slice_t
            last = t
            
            end_of_this_slice = t +  self.slices[t].getDuration()

            feasible = end_of_this_slice > start_time and self.slices[t].getFreeNodes() >= job.nodes
            
            if not feasible: # then surely the job cannot be assigned to this slice  
                partially_assigned = False
                accumulated_duration = 0
                continue
            
            if feasible and not partially_assigned: 
                # we'll check if the job can be assigned to this slice and perhaps to its successive 
                partially_assigned = True
                accumulated_duration = t + self.slices[t].getDuration() - start_time
                tentative_start_time =  max(start_time, t)
                if accumulated_duration >= job.duration:
                    return tentative_start_time
                continue
                
            # at this point: it's a feasible slice and the job is partially_assigned:
            accumulated_duration += self.slices[t].getDuration()
            if accumulated_duration >= job.duration:
                return tentative_start_time
            continue
            
            # end of for loop, we've examined all existing slices
            
        if partially_assigned: 
            return tentative_start_time
             
        return max(start_time, last + self.slices[last].getDuration()) # the job can be assigned right after the last slice or later 

        
            
    def assignJob(self, job, assignment_time):         
        """ assigns the job to start at the given assignment time.

        Important assumption: assignment_time was returned by jobEarliestAssignment. """

        job.start_to_run_at_time = assignment_time
        
        if len(self.slices) == 0: # no current job assignments, all nodes are free
            self.addNewJobToNewSlice(assignment_time, job.duration, job)
            return

        if not self.slices.has_key(assignment_time): #in case the job is assigned to the "middle" of a slice we would
            # like to split the slice accordingly in this preprocessing stage         
            times = self.slices.keys() #*** I couldn't do the sorting nicely as Ori suggested 
            times.sort()

            last = 0
            
            for t in times: #preprocessing stage: to ensure that the assignment time will start at a begining of a slice
                last = t #in case that assignment_time <= the_end_of_last current existing slice  
                end_of_this_slice = t +  self.slices[t].getDuration()
                duration_of_this_slice = self.slices[t].getDuration()
            
                if end_of_this_slice < assignment_time:
                    continue

                if end_of_this_slice == assignment_time:
                    break
                
                # splitting slice t with respect to the assignment time 
                jobs = self.slices[t].getJobs()
                newslice = CpuTimeSlice(t, assignment_time - t, jobs)
                self.slices[t] = newslice
                newslice = CpuTimeSlice(assignment_time, end_of_this_slice - assignment_time, jobs)
                self.slices[assignment_time] = newslice
                break ## maybe this block can be deindented 


            end_of_last_slice = last + self.slices[last].getDuration() # in the following
                                                                       # case there's no need to itterate through the slices
            if end_of_last_slice < assignment_time: #we add an intermediate "empty" slice to maintain the "continuity" of slices
                newslice = CpuTimeSlice(end_of_last_slice, assignment_time - end_of_last_slice, {})
                self.slices[end_of_last_slice] = newslice
                self.addNewJobToNewSlice(assignment_time, job.duration, job) 
                return 
            
                
        #itteration through the slices 
         
        times = self.slices.keys() #*** I couldn't do the sorting nicely as Ori suggested 
        times.sort()

        remained_duration = job.duration
        
        for t in times:
            last = t 
            duration_of_this_slice = self.slices[t].getDuration()
            
            if t < assignment_time: # skip this slice 
                continue
            
            if  duration_of_this_slice <= remained_duration: # just add the job to the current slice
                self.slices[t].addJob(job)
                remained_duration = remained_duration - self.slices[t].getDuration()
                if remained_duration == 0:
                    return
                continue
            
                   
            #else: duration_of_this_slice > remained_duration :
            jobs = self.slices[t].getJobs()

            newslice = CpuTimeSlice(t, remained_duration, jobs)
            newslice.addJob(job)
            self.slices[t] = newslice

            newslice = CpuTimeSlice(t + remained_duration, duration_of_this_slice - remained_duration, jobs)
            self.slices[t + remained_duration] = newslice
            return
            
        # end of for loop, we've examined all existing slices and if this point is reached
        # we must add a new "tail" slice for the remaining part of the job
            
        end_of_last_slice = last + self.slices[last].getDuration()
        self.addNewJobToNewSlice(end_of_last_slice, remained_duration, job)
        return

    
    def addNewJobToNewSlice(self, time, duration, job):
        job_entry = {job.id : job.nodes}
        newslice = CpuTimeSlice(time, duration, job_entry)
        self.slices[time] = newslice 


    def delJobFromCpuSlices(self, job):
        times = self.slices.keys() #*** I couldn't do the sorting nicely as Ori suggested 
        times.sort()
        
        job_found = False
        
        for t in times:
            if self.slices[t].isMemeber(job):
                job_found = True
                self.slices[t].delJob(job)
            else:
                if job_found:
                    return
        return


    def delTailofJobFromCpuSlices(self, job):
        """ This function is used when the actual duration is smaller than the duration, so the tail
        of the job must be deleted from the slices
        Assumption: job is assigned to successive slices. Specifically, there are no preemptions."""
        times = self.slices.keys() #*** I couldn't do the sorting nicely as Ori suggested 
        times.sort()

        accumulated_duration = 0
        tail_of_the_job = False 


        for t in times:
            duration_of_this_slice = self.slices[t].getDuration()
            
            if self.slices[t].isMemeber(job):
                accumulated_duration += duration_of_this_slice

            if accumulated_duration <= job.actual_duration:
                continue
            
            # at this point accumulated_duration > job.actual_duration:
            if not tail_of_the_job:          
                tail_of_the_job = True 
                delta = accumulated_duration - job.actual_duration 
                # splitting slice t with respect to delta and removing the job from the later slice
                jobs = self.slices[t].getJobs()
                newslice = CpuTimeSlice(t, duration_of_this_slice - delta , jobs)
                self.slices[t] = newslice
                
                split_time = t + duration_of_this_slice - delta
                newslice = CpuTimeSlice(split_time, delta , jobs)
                newslice.delJob(job)                
                self.slices[split_time] = newslice

                if accumulated_duration >= job.duration: #might delete this if i'll use python 2.4 with sorted()
                    return
                else: 
                    continue
                 
            self.slices[t].delJob(job) # removing the job from the remaining slices in the "tail"
               
            if accumulated_duration >= job.duration:                
                return
            
               
    
             
    def printCpuSlices(self):
        if len(self.slices) == 0:
            print "There are no slices to print"
        times = self.slices.keys()
        times.sort()
        for t in times: 
            print self.slices[t]
        print
        





            
        
        





"""
job10 = Job('job10', 1000, 50, 0)
job15 = Job('job15', 1000, 10, 10)
job18 = Job('job18', 1000, 50, 20)
job19 = Job('job19', 1000, 10, 30)


print "start_time, duration, free_nodes, jobs"
print
print
print

scheduler = ConservativeScheduler(100)
scheduler.cpu_snapshot.printCpuSlices()

scheduler.addJob(job10, job10.arrival_time)
scheduler.cpu_snapshot.printCpuSlices()

print


scheduler.addJob(job15, job15.arrival_time)
scheduler.cpu_snapshot.printCpuSlices()

print


scheduler.addJob(job18, job18.arrival_time)
scheduler.cpu_snapshot.printCpuSlices()

print

scheduler.addJob(job19, job19.arrival_time)
scheduler.cpu_snapshot.printCpuSlices()

print


cs.delJobFromCpuSlices(job15)

cs.printCpuSlices()
print


"""
