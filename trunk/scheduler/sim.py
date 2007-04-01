

class Job:

    def __init__(self, job_id, user_predicted_duration, job_nodes, \
                 job_arrival_time=0, job_actual_duration=0):

        assert job_nodes > 0
        assert user_predicted_duration >= 0
        assert job_actual_duration >= 0 

        self.id = job_id
        self.user_predicted_duration = user_predicted_duration
        self.nodes = job_nodes
        self.arrival_time = job_arrival_time # Assumption: arrival time is greater than zero 
        self.start_to_run_at_time = -1 
        self.actual_duration = job_actual_duration
        

    def __str__(self):
        return str(self.id) + ", arrival=" + str(self.arrival_time) + \
               ", dur=" + str(self.user_predicted_duration) + ",act_dur=" + str(self.actual_duration) + \
               ", #nodes=" + str(self.nodes) + \
               ", startTime=" + str(self.start_to_run_at_time)  
    
        

class CpuTimeSlice:
    ''' represents a "tenatative feasible" snapshot of the cpu between the start_time until start_time + dur_time.
        It is tentative since a job might be rescheduled to an earlier slice. It is feasible since the total demand
        for nodes ba all the jobs assigned to this slice never exceeds the amount of the total nodes available.
        Assumption: the duration of the slice is never changed. We can replace this slice with a new slice with shorter duration.'''
    
    total_nodes = 0 # a class variable
    
    def __init__(self, start_time=0, duration=1, jobs=[]):
        assert duration > 0
        self.start_time = start_time
        self.duration = duration
        self.jobs = []
  
        
        if len(jobs) == 0:  
            self.free_nodes = CpuTimeSlice.total_nodes
           
        else:
            num_of_active_nodes = 0
            for job in jobs: num_of_active_nodes += job.nodes
            self.free_nodes = CpuTimeSlice.total_nodes - num_of_active_nodes 
            for job in jobs: # by value ... 
                self.jobs.append(job)
                
           
             
    def __str__(self):
        jobs_str = ""
        for job in self.jobs:
            jobs_str += ", [" + str(job.id) + ", " + str(job.nodes) + "]"    
        return '%d %d %d %s' % (self.start_time, self.duration, self.free_nodes, jobs_str)


            
    def addJob(self, job):
        assert self.free_nodes >= job.nodes
        self.free_nodes -= job.nodes
        self.jobs.append(job)


    def delJob(self, job):
        self.free_nodes += job.nodes
        assert self.free_nodes <= CpuTimeSlice.total_nodes
        self.jobs.remove(job)


    def isMemeber(self, job):
        if job in self.jobs:
            return True
        else: 
            return False
        

    def getJobs(self):
        return self.jobs 
    
    def getDuration(self):
        return self.duration

    def getFreeNodes(self):
        return self.free_nodes
    

        
        
class CpuSnapshot(object):
    """ represents the time table with the assignments of jobs to available nodes. """
    
    def __init__(self, total_nodes=100):
        CpuTimeSlice.total_nodes = total_nodes
        self.total_nodes = total_nodes
        self.slices={} # initializing the main structure of this class 
        self.slices[0] = CpuTimeSlice() # Assumption: the snapshot always has at least one slice 
        
               
    def jobEarliestAssignment(self, job, time=0):
        """ returns the earliest time right after the given time for which the job can be assigned
        enough nodes for job.user_predicted_duration unit of times in an uninterrupted fashion.
        Assumption: number of requested nodes is not greater than number of total nodes.
        Assumption: time >=  the arrival time of the job >= 0."""
        
        partially_assigned = False         
        tentative_start_time = 0 
        accumulated_duration = 0
        
        assert time >= 0
        assert time >= job.arrival_time
        
        for t in self._sorted_times: # continuity assumption: if t' is the successor of t, then: t' = t + duration_of_slice_t
            
            end_of_this_slice = t +  self.slices[t].getDuration()

            feasible = end_of_this_slice > time and self.slices[t].getFreeNodes() >= job.nodes
            
            if not feasible: # then surely the job cannot be assigned to this slice
                print "aaaaa"
                partially_assigned = False
                accumulated_duration = 0
                        
            elif feasible and not partially_assigned:
                print "bbbb"
                # we'll check if the job can be assigned to this slice and perhaps to its successive 
                partially_assigned = True
                tentative_start_time =  max(time, t)
                accumulated_duration = end_of_this_slice - tentative_start_time

            else:
                print "cccc"
                # it's a feasible slice and the job is partially_assigned:
                accumulated_duration += self.slices[t].getDuration()
            
            if accumulated_duration >= job.user_predicted_duration:
                print "dddddddd"
                return tentative_start_time
    
            # end of for loop, we've examined all existing slices
            
        if partially_assigned: #and so there are not enough slices in the tail, then:
            print "eeeeee"
            return tentative_start_time

        # otherwise, the job will be assigned right after the last slice or later
        print "fffffff"
        last_slice_start_time = self._sorted_times[-1]
        last_slice_end_time = last_slice_start_time +  self.slices[last_slice_start_time].getDuration()
        return max(time, last_slice_end_time)  



    def _ensure_a_slice_starts_at(self, assignment_time):
        """ A preprocessing stage: to ensure that the assignment time of the new added job will start at a begining of a slice """

        if assignment_time in self.slices:
            return # we already have such a slice 
        
        last_slice_start_time = self._sorted_times[-1]
        last_slice_end_time = last_slice_start_time +  self.slices[last_slice_start_time].getDuration()

        if last_slice_end_time < assignment_time: #we add an intermediate "empty" slice to maintain the "continuity" of slices
            self._add_slice( CpuTimeSlice(last_slice_end_time, assignment_time - last_slice_end_time, {}) )
            self._add_slice( CpuTimeSlice(assignment_time, duration=1, jobs={}) ) # duration is arbitrary here
            return
        
        if last_slice_end_time == assignment_time:
            self._add_slice( CpuTimeSlice(assignment_time, duration=1, jobs={}) ) # duration is arbitrary here
            return


        for t in self._sorted_times:
        
            end_of_this_slice = t +  self.slices[t].getDuration()
            duration_of_this_slice = self.slices[t].getDuration()

            if end_of_this_slice < assignment_time:
                continue

            # splitting slice t with respect to the assignment time
            jobs = self.slices[t].getJobs()
            self._add_slice( CpuTimeSlice(t, assignment_time - t, jobs) )
            self._add_slice( CpuTimeSlice(assignment_time, end_of_this_slice - assignment_time, jobs) )
            return 


      
    def _add_job_to_relevant_slices(self, job):
        assignment_time = job.start_to_run_at_time     
        remained_duration = job.user_predicted_duration

        for slice_start_time in self._slice_start_times_beginning_at(assignment_time):
            if  self._slice_duration(slice_start_time) <= remained_duration: # just add the job to the current slice
                self.slices[slice_start_time].addJob(job)
                remained_duration = remained_duration - self.slices[slice_start_time].getDuration()
                if remained_duration == 0:
                    return
                continue
            
                   
            #else: duration_of_this_slice > remained_duration, that is the current slice
            #is longer than what we actually need, we thus split the slice, then add the job to the 1st one, and return
            
            self._add_slice(
                CpuTimeSlice(
                    start_time = slice_start_time + remained_duration,
                    duration   = self._slice_duration(slice_start_time) - remained_duration,
                    jobs       = self.slices[slice_start_time].getJobs(),
                )
                )
            
            newslice = CpuTimeSlice(
                start_time = slice_start_time,
                duration   = remained_duration,
                jobs       = self.slices[slice_start_time].getJobs(),
                )
            newslice.addJob(job)
            self._add_slice(newslice)
                
            return
            
        # end of for loop, we've examined all existing slices and if this point is reached
        # we must add a new "tail" slice for the remaining part of the job

        last_slice_start_time = self._sorted_times[-1]
        end_of_last_slice = last_slice_start_time + self.slices[last_slice_start_time].getDuration()
        self.addNewJobToNewSlice(end_of_last_slice, remained_duration, job)
        return
        

    def assignJob(self, job, assignment_time):         
        """ assigns the job to start at the given assignment time.
        
        Important assumption: assignment_time was returned by jobEarliestAssignment. """
        job.start_to_run_at_time = assignment_time
        self._ensure_a_slice_starts_at(assignment_time)
        self._add_job_to_relevant_slices(job)



    def _add_slice(self, slice):
        self.slices[slice.start_time] = slice
        
        
    def _slice_start_times_beginning_at(self, time):
        "yields only the slice start times after the given time"
        return (x for x in self._sorted_times if x >= time)

    
    def _slice_duration(self, start_time):
        return self.slices[start_time].getDuration()


    @property
    def _sorted_times(self):
        return sorted(self.slices.keys())

    
    def addNewJobToNewSlice(self, time, duration, job):
        jobs = []
        jobs.append(job)
        self._add_slice(CpuTimeSlice(time, duration, jobs) )


    def delJobFromCpuSlices(self, job):        
        """ Deletes an entire job from the slices.
        Assumption: job resides at consecutive slices (no preemptions) """

        job_found = False

        for t in self._sorted_times:
            if self.slices[t].isMemeber(job):
                job_found = True
                self.slices[t].delJob(job)
            else:
                if job_found:
                    return
        return



    def delTailofJobFromCpuSlices(self, job):
        """ This function is used when the actual duration is smaller than the predicted duration, so the tail
        of the job must be deleted from the slices.
        We itterate trough the sorted slices until the critical point is found: the point from which the
        tail of the job starts. 
        Assumption: job is assigned to successive slices. Specifically, there are no preemptions."""

        accumulated_duration = 0
        critical_point_is_found = False 
        

        for t in self._sorted_times:
            duration_of_this_slice = self.slices[t].getDuration()
            
            if self.slices[t].isMemeber(job):
                accumulated_duration += duration_of_this_slice

            if accumulated_duration == job.actual_duration:
                critical_point_is_found = True                   

            # when we just found the critical point 
            elif accumulated_duration > job.actual_duration and not critical_point_is_found:
                
                critical_point_is_found = True 
                # split current slice with respect to delta and remove the job from the later slice
                delta = accumulated_duration - job.actual_duration
                jobs = self.slices[t].getJobs()

                newslice = CpuTimeSlice(t, duration_of_this_slice - delta, jobs)
                self._add_slice(newslice)
                
                split_time = t + duration_of_this_slice - delta
                newslice = CpuTimeSlice(split_time, delta, jobs)
                newslice.delJob(job)
                self._add_slice(newslice)
                
            #we already found the critical point, so the job should be removed entirly from this slice
            elif accumulated_duration > job.actual_duration and critical_point_is_found:
                self.slices[t].delJob(job) 
  
                
            if accumulated_duration >= job.user_predicted_duration:
                return


            
    def CpuSlicesTestFeasibility(self):
        duration = 0
        time = 0
        scheduled_jobs_start_slice = {}
        scheduled_jobs_last_slice = {}
        scheduled_jobs_accumulated_duration = {}
        scheduled_jobs = {}
        
        for t in self._sorted_times:
            free_nodes = self.slices[t].getFreeNodes()
            prev_duration = duration
            prev_t = time
            
            if free_nodes < 0: 
                print ">>> PROBLEM: free nodes is a negative number, in slice", t
                return False
            
            if free_nodes > self.total_nodes:
                print ">>> PROBLEM: free nodes exceeds number of available nodes ...."
                return False

            num_of_active_nodes = 0
            
            for job in self.slices[t].jobs:
                num_of_active_nodes += job.nodes
                
                if scheduled_jobs_start_slice.has_key(job.id):
                    scheduled_jobs_last_slice[job.id] = t
                    scheduled_jobs_accumulated_duration[job.id] += self.slices[t].getDuration() 
                else:
                    if t != job.start_to_run_at_time:
                        print ">>> PROBLEM: start time: ", job.start_to_run_at_time, " of job", job.id, "is:", t
                        return False
                    scheduled_jobs[job.id] = job
                    scheduled_jobs_start_slice[job.id] = t
                    scheduled_jobs_last_slice[job.id] = t
                    scheduled_jobs_accumulated_duration[job.id] = self.slices[t].getDuration()
                    
            if num_of_active_nodes != self.total_nodes - free_nodes:
                print ">>> PROBLEM: wrong number of free nodes in slice", t 
                return False
            
            if t != prev_t + prev_duration:
                print ">>> PROBLEM: non scuccessive slices", t, prev_t 
                return False
                
            duration = self.slices[t].getDuration()
            time = t

        for job_id, job_start_slice in scheduled_jobs_start_slice.iteritems():
            job_last_slice =  scheduled_jobs_last_slice[job_id]
            duration_of_job = job_last_slice + self.slices[job_last_slice].getDuration() - job_start_slice
            print job_id, "start_slice, last_slice, duration_last:", \
                  job_start_slice, job_last_slice, self.slices[job_last_slice].getDuration()
            if duration_of_job != scheduled_jobs[job_id].actual_duration:
                print ">>>PROBLEM: with actual duration of job: ", \
                      job.actual_duration, "vs.", duration_of_job,  " of job", job_id
                return False
            """
            if duration_of_job != scheduled_jobs_accumulated_duration[job.id]:
                print ">>>PROBLEM: with actual duration of job:", \
                      scheduled_jobs_accumulated_duration[job.id], "vs.", duration_of_job,  " of job", job_id
                return False
            """

        print "TEST is OK!!!!" 
        return True
    
            
            
    
             
    def printCpuSlices(self):

        print "start time | duration | #free nodes | { job.id : #job.nodes }"            
        for t in self._sorted_times: 
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