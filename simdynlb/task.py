"""
Class represent Task with its code entry, data, and childs (if yes).
    - tid: unique id of each task
    - dur: duration or wallclock execution time of a task
    - data: data size or arguments of a task
    - sta_time: to be executed
    - end_time: to be termintated
    - mig_time: to be migrated
    - local_node: the original node
    - remot_node: the remote node
"""
class Task:
    def __init__(self, tid, dur, data, node):
        self.tid = tid
        self.dur = dur
        self.data = data
        # other info that can be configured while queueing
        self.sta_time = 0.0
        self.end_time = 0.0
        self.mig_time = 0.0
        self.arr_time = 0.0
        self.local_node = node
        self.remot_node = -1
            
    def set_time(self, s_time, e_time):
        self.sta_time = s_time
        self.end_time = e_time

    def set_remote_node(self, rnode):
        self.remot_node = rnode
        
    def set_mig_time(self, mig_time):
        self.mig_time = mig_time
    
    def set_arr_time(self, arr_time):
        self.arr_time = arr_time
        
    def get_dur(self):
        return self.dur
        
    def get_end_time(self):
        return self.end_time
    
    def print_task_info(self):
        print('Task {}: dur({}), data({}), start_end_time({}-{})'.format(self.tid,
                self.dur, self.data, self.sta_time, self.end_time))
        