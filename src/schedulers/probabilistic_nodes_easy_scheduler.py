from common import CpuSnapshot
from probabilistic_easy_scheduler import ProbabilisticEasyScheduler
from math import log


def job_key(job):
    rounded_up_processors = pow(2, int(log(max(2 * job.num_required_processors - 1, 1), 2)))
    return str(job.user_id)+str(rounded_up_processors)
        
class  ProbabilisticNodesEasyScheduler(ProbabilisticEasyScheduler):
    """ This algorithm implements a version of Feitelson and Nissimov, June 2007
        In this version we the distribution is based on the user_id,
        and also on the number of the processores required. Specifically,
        we bunch together all jobs by the same user with a similar number of processors (using a lograthmic scale)
        see the job_key function above
    """
    
    def __init__(self, num_processors, threshold = 0.05):
        super(ProbabilisticNodesEasyScheduler, self).__init__(num_processors)
        self.threshold = threshold
 