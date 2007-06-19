from common import CpuSnapshot
from base.prototype import JobStartEvent

from easy_scheduler import EasyBackfillScheduler

class  BasicCompareFunctions(object):

    def cmp0(self, job_a, job_b):
        return cmp(job_b.submit_time, job_a.submit_time)
        
    def cmp1(self, job_a, job_b):
        return cmp(job_a.submit_time, job_b.submit_time)

    def cmp2(self, job_a, job_b):
        return cmp (job_a.num_processors, job_b.num_processors)

    def cmp3(self, job_a, job_b):
        return cmp(job_a.estimated_run_time, job_b.estimated_run_time)

    def cmp4(self, job_a, job_b):
        return cmp(job_a.num_processors * job_a.estimated_run_time, job_b.num_processors * job_b.estimated_run_time)


class BasicLocalEvaluationFuction(object):

    def value(self, list_of_jobs):
        val = 0.0
        for job in list_of_jobs:
             val += job.num_processors * job.estimated_run_time  
        return val
    
    
class  GreedyEasyBackFillScheduler(EasyBackfillScheduler):
    def __init__(self, num_processors, list_of_compare_functions=None, value_function=None):
        EasyBackfillScheduler.__init__(self, num_processors)
        
        self.list_of_compare_functions = []
        if list_of_compare_functions == None:
            bf = BasicCompareFunctions()
            self.list_of_compare_functions = [bf.cmp0, bf.cmp1, bf.cmp2, bf.cmp3]
        else:
            self.list_of_compare_functions = list_of_compare_functions
                
        if value_function == None:
            bv = BasicLocalEvaluationFuction()
            self.value_function = bv.value
        else:
            self.value_function = value_function
            

    def _schedule_jobs(self, current_time):
        # Maui's scheduling methods are based on the analogue methods of EasyBackfill.
        # The additonal or different code lines are marked with ## +
        if len(self.waiting_list_of_unscheduled_jobs) == 0:
            return []

        self.waiting_list_of_unscheduled_jobs.sort(self.submit_time_compare) ## +

        newEvents = self._schedule_the_head_of_the_waiting_list(current_time)  # call the method of EasyBackfill 
        newEvents += self._schedule_the_tail_of_the_waiting_list(current_time)  # override the method of EasyBackfill (see below)

        self.waiting_list_of_unscheduled_jobs.sort(self.submit_time_compare) ## +
        return newEvents

    def _schedule_the_tail_of_the_waiting_list(self, current_time):
        """
        Updates the internal state and returns a list of new events
        """
        if len(self.waiting_list_of_unscheduled_jobs) <= 1:
            return []

        self._find_an_approximate_best_order_of_the_jobs(current_time) ## +
        print self.cpu_snapshot.printCpuSlices(); self.print_waiting_list()  # XXX

        result = []
        jobs_to_remove = []
        for job in self.waiting_list_of_unscheduled_jobs:
            earliest_time = self.cpu_snapshot.jobEarliestAssignment(job, current_time)
            print "______", job, earliest_time # XXX
            if current_time == earliest_time: 
                jobs_to_remove.append(job)
                self.cpu_snapshot.assignJob(job, current_time)
                result.append( JobStartEvent(current_time, job) )
                                                                                
        for job in jobs_to_remove:
            self.waiting_list_of_unscheduled_jobs.remove(job)

        return result


    def _find_an_approximate_best_order_of_the_jobs(self, current_time):
        first_job = self.waiting_list_of_unscheduled_jobs.pop(0) ## +
        shadow_time = self.cpu_snapshot.jobEarliestAssignment(first_job, current_time)
        self.cpu_snapshot.assignJob(first_job, shadow_time)

        index_of_rank_with_max_value = 0
        max_value = 0.0
        for index in range(len(self.list_of_compare_functions)):
            tmp_cpu_snapshot = self.cpu_snapshot.clone()
            tentative_list_of_jobs = []
            self.waiting_list_of_unscheduled_jobs.sort(self.list_of_compare_functions[index])
            for job in self.waiting_list_of_unscheduled_jobs:
                earliest_time = tmp_cpu_snapshot.jobEarliestAssignment(job, current_time) 
                if current_time == earliest_time:
                    tmp_cpu_snapshot.assignJob(job, current_time)
                    tentative_list_of_jobs.append(job)

            value = self.value_function(tentative_list_of_jobs)
            if max_value < value:
                max_value = value
                index_of_rank_with_max_value = index
                
        self.cpu_snapshot.delJobFromCpuSlices(first_job)
        self.waiting_list_of_unscheduled_jobs.sort(self.list_of_compare_functions[index_of_rank_with_max_value])
        self.waiting_list_of_unscheduled_jobs.append(first_job)
            


    def submit_time_compare(self, job_a, job_b):
        return cmp(job_a.submit_time, job_b.submit_time) 


    def print_waiting_list(self):
        for job in self.waiting_list_of_unscheduled_jobs:
            print job
        print
