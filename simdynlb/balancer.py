import numpy as np
import random

"""Balancing interface for taking decision when we migrate tasks
    - run on a separate thread
    - check on-the-fly the status of queues
"""

"""Class Message for exchanging steal request and accept
    - sender: the rank who sends message
    - receiver: the rank who receives message. If -1, it means to all
    - info: e.g., 'steal_request', 'steal_accept'
    - send_time: time when the message is sent
    - recv_time: time when the message is arrived/received
"""
class Message:
    def __init__(self, sender, receiver, info):
        self.sender = sender
        self.receiver = receiver
        self.info = info
        # other info that can be configured while queueing
        self.send_time = 0.0
        self.recv_time = 0.0
            
    def set_time(self, send_time, recv_time):
        self.send_time = send_time
        self.recv_time = recv_time
    
    def print_msg_info(self):
        print('Message: sender({}), receiver({}), info({}), time(send-{} - recv-{})'.format(self.sender,
                self.receiver, self.info, self.send_time, self.recv_time))

# -----------------------------------------------------
# Constant Definition
# -----------------------------------------------------
MIN_REL_LOAD_IMBALANCE = 0.05
MIN_TASKS_IN_QUEUE_FOR_OFFLOAD = 2
MIN_TASKS_IN_QUEUE_FOR_STEAL = 2
MIN_ABS_LOAD_DIFFERENCE = 2
LATENCY = 2

# -----------------------------------------------------
# Util Functions
# -----------------------------------------------------
def check_imbalance_status(clock, local_queues, arr_being_exe_tasks):
    num_procs = len(local_queues)
    num_tasks_being_executed = 0
    queue_sizes = []
    for i in range(num_procs):
        queue_sizes.append(len(local_queues[i]))
        if arr_being_exe_tasks[i] != None:
            num_tasks_being_executed += 1

    # calculate Rimb
    lmin = np.min(queue_sizes)
    lmax = np.max(queue_sizes)
    lavg = np.average(queue_sizes)
    Rimb_avg = 0.0
    Rimb_minmax = 0.0
    if lavg != 0 and lmax != 0:
        Rimb_avg = (lmax - lavg) / lavg
        Rimb_minmax = (lmax - lmin) / lmax

    # show queue status
    # print("[Tcomm] Clock[{}], Rimb_minmax={:5.2f}, Q_size=[{},{},{},{},{},{},{},{}]".format(clock, Rimb_minmax, 
    #     queue_sizes[0], queue_sizes[1], queue_sizes[2], queue_sizes[3],
    #     queue_sizes[4], queue_sizes[5], queue_sizes[6], queue_sizes[7]))

    return Rimb_minmax

def check_queue_status(clock, num_procs, local_queues, arr_num_tasks_before_execution):
    arr_empty_queues = []
    arr_busy_queues = []
    for r in range(num_procs):
        current_rank = r
        queue_size = len(local_queues[r])
        if queue_size == 0:
            arr_empty_queues.append([current_rank, queue_size])
        else:
            arr_busy_queues.append([current_rank, queue_size])
    return [arr_empty_queues, arr_busy_queues]


def exchange_steal_request(clock, arr_queue_status, arr_steal_request_msg, arr_steal_accept_msg):
    
    # side of processes with EMPTY queue
    empty_queues = arr_queue_status[0]
    if len(empty_queues) != 0:
        for i in range(len(empty_queues)):
            idle_rank = empty_queues[i][0]
            # check if this rank has not sent any requests
            if len(arr_steal_request_msg[idle_rank]) == 0:
                request_msg = Message(idle_rank, -1, 'steal_request')
                request_msg.set_time(clock, clock+LATENCY)
                arr_steal_request_msg[idle_rank].append(request_msg)
                print('[DEBUG] Clock {:5d}: R{:2d} SENDS steal_request (sent at {:5d}, will recv at {:5d})'.format(
                        clock, idle_rank, clock, clock+LATENCY
                ))
            # TODO: 

    # side of processes with BUSY queue
    busy_queues = arr_queue_status[1]
    if len(busy_queues) != 0:
        for i in range(len(busy_queues)):

            # check the busy rank
            busy_rank = busy_queues[i][0]
            busy_rank_queue_size = busy_queues[i][1]

            # check the current steal-request messages have sent and arrived
            list_idle_ranks = []
            for j in range(len(arr_steal_request_msg)):
                if len(arr_steal_request_msg[j]) != 0:
                    req_msg = arr_steal_request_msg[j][0]
                    if req_msg.info == 'steal_request' and req_msg.recv_time == clock:
                        list_idle_ranks.append(j)

            # check if this rank has not replied any requests
            if len(arr_steal_accept_msg[busy_rank]) == 0:
                # random select an idle pocess
                if len(list_idle_ranks) != 0 and busy_rank_queue_size >= MIN_TASKS_IN_QUEUE_FOR_STEAL:
                    selected_idle_rank = random.choice(list_idle_ranks)
                    # change the steal request message info
                    checkout_req_msg = arr_steal_request_msg[selected_idle_rank][0]
                    checkout_req_msg.info = 'waiting'
                    # put the steal accept message in
                    accept_msg = Message(busy_rank, selected_idle_rank, 'steal_accept')
                    accept_msg.set_time(clock, clock+LATENCY)
                    arr_steal_accept_msg[busy_rank].append(accept_msg)
                    print('[DEBUG] Clock {:5d}: R{:2d} CONFIRMS steal_accept for R{:2d} (sent at {:5d}, will recv at {:5d})'.format(
                        clock, busy_rank, selected_idle_rank, clock, clock+LATENCY
                    ))
            else:
                if len(list_idle_ranks) != 0 and busy_rank_queue_size >= MIN_TASKS_IN_QUEUE_FOR_STEAL:
                    selected_idle_rank = random.choice(list_idle_ranks)
                    # change the steal request message info
                    checkout_req_msg = arr_steal_request_msg[selected_idle_rank][0]
                    checkout_req_msg.info = 'waiting'
                    # put the steal accept message in
                    accept_msg = Message(busy_rank, selected_idle_rank, 'steal_accept')
                    accept_msg.set_time(clock, clock+LATENCY)
                    arr_steal_accept_msg[busy_rank].append(accept_msg)
                    print('[DEBUG] Clock {:5d}: R{:2d} RE-CONFIRMS steal_accept for R{:2d} (sent at {:5d}, will recv at {:5d})'.format(
                        clock, busy_rank, selected_idle_rank, clock, clock+LATENCY
                    ))

def recv_steal_accept(clock, arr_queue_status, arr_steal_request_msg, arr_steal_accept_msg):
    # side of processes with EMPTY queue
    empty_queues = arr_queue_status[0]
    if len(empty_queues) != 0:
        for i in range(len(empty_queues)):
            idle_rank = empty_queues[i][0]
            list_steal_accepted_ranks = []
            # check the processes which have confirmed for the steal reques
            for j in range(len(arr_steal_accept_msg)):
                if len(arr_steal_accept_msg[j]) != 0:
                    checkout_accept_msg = arr_steal_accept_msg[j][0]
                    accepted_rank = checkout_accept_msg.receiver
                    arrived_time = checkout_accept_msg.recv_time
                    if accepted_rank == idle_rank and arrived_time == clock:
                        list_steal_accepted_ranks.append(j)
            # choose rank for stealing tasks
            if len(list_steal_accepted_ranks) != 0:
                selected_busy_rank = random.choice(list_steal_accepted_ranks)
                # change the message status
                checkout_req_msg = arr_steal_request_msg[idle_rank][0]
                checkout_req_msg.info = 'stealing_task'
                checkout_req_msg.receiver = selected_busy_rank

                checkout_ack_msg = arr_steal_accept_msg[selected_busy_rank][0]
                checkout_ack_msg.info = 'sending_task'
                print('[DEBUG] Clock {:5d}: R{:2d} will STEAL task from R{:2d}'.format(
                        clock, idle_rank, selected_busy_rank
                    ))


# -----------------------------------------------------
# Debug Functions
# -----------------------------------------------------
def show_sorted_load(clock, sortLCQ, local_queues):
    str_R = ""
    str_L = ""
    for i in sortLCQ:
        str_R += str(i) + ","
        str_L += str(len(local_queues[i])) + ","
    print("[Tcomm] clock[{}]: R{}, L={}...".format(clock, str_R, str_L))

# -----------------------------------------------------
# Balancing Functions
# -----------------------------------------------------

def react_task_offloading(clock, num_procs, Rimb, local_queues, arr_num_tasks_before_execution, arr_victim_offloader):
    
    # check the imb condition
    if Rimb >= MIN_REL_LOAD_IMBALANCE:

        # check queue sizes
        queue_sizes = []
        for i in range(num_procs):
            queue_sizes.append(len(local_queues[i]))

        # sort the queue sizes
        sortLCQ = np.argsort(queue_sizes)
        # show_sorted_load(clock, sortLCQ, local_queues)
        
        # select offloader-victim
        for i in range(int(num_procs/2), num_procs):
            offloader_rank = sortLCQ[i]
            victim_rank = sortLCQ[num_procs-i-1]

            offloader_qsize = len(local_queues[offloader_rank])
            victim_qsize = len(local_queues[victim_rank])

            diff_load = abs(offloader_qsize - victim_qsize)

            # check the number of selected tasks for migration at the moment
            num_offload_candidates = len(arr_victim_offloader[offloader_rank])

            # if ok, select more tasks for offloading
            if diff_load > MIN_ABS_LOAD_DIFFERENCE and \
                offloader_qsize > MIN_TASKS_IN_QUEUE_FOR_OFFLOAD and \
                num_offload_candidates < arr_num_tasks_before_execution[offloader_rank]:

                # a pair of offloader-victim
                offload_victim = [offloader_rank, victim_rank]
                arr_victim_offloader[offloader_rank].append(offload_victim)
                # print("[Tcomm] clock[{}]: offloader={}, victim={}...".format(clock, off_vic[0], off_vic[1]))
    return 0