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
        # for time to send/recv messages
        self.send_time = 0.0
        self.recv_time = 0.0
        # for marking nodes accept a request
        self.accept_rank = -1
            
    def set_time(self, send_time, recv_time):
        self.send_time = send_time
        self.recv_time = recv_time

    def set_accept_proc(self, rank):
        self.accept_rank = rank
    
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

def check_queue_status(clock, num_procs, local_queues):
    arr_empty_queues = []
    arr_busy_queues = []
    for r in range(num_procs):
        current_rank = r
        queue_size = len(local_queues[r])
        if queue_size == 0:
            arr_empty_queues.append([current_rank, queue_size])
        elif queue_size > MIN_TASKS_IN_QUEUE_FOR_STEAL:
            arr_busy_queues.append([current_rank, queue_size])
    return [arr_empty_queues, arr_busy_queues]


def exchange_steal_request(clock, arr_queue_status, arr_request_msg, arr_accept_msg):
    # check empty and busy queues
    empty_queues = arr_queue_status[0]
    busy_queues = arr_queue_status[1]

    # -------------------------------------
    # IDLE processes
    # -------------------------------------
    if len(empty_queues) != 0 and len(busy_queues) != 0:
        for i in range(len(empty_queues)):
            idle_rank = empty_queues[i][0]
            # check if this rank has not sent any requests
            if len(arr_request_msg[idle_rank]) == 0:
                request_msg = Message(idle_rank, -1, 'steal_request')
                request_msg.set_time(clock, clock+LATENCY)
                arr_request_msg[idle_rank].append(request_msg)
                print('[DEBUG] Clock {:5d}: R{:2d} SENDS steal_request (sent at {:5d}, will recv at {:5d})\n'.format(
                        clock, idle_rank, clock, clock+LATENCY
                ))
                
            # check if this rank has already sent a request but not selected, then we re-send it
            else:
                checkout_req_msg = arr_request_msg[idle_rank][0]
                if checkout_req_msg.info == 'steal_request' and checkout_req_msg.recv_time < clock:
                    checkout_req_msg.set_time(clock, clock) # renew time
                    print('[DEBUG] Clock {:5d}: R{:2d} RE-SENDS steal_request (sent at {:5d}, will recv at {:5d})\n'.format(
                            clock, idle_rank, checkout_req_msg.send_time, checkout_req_msg.recv_time
                    ))

        # -------------------------------------
        # BUSY processes
        # -------------------------------------
        # check ranks with the current steal-request message has been sent and arrived
        list_idle_ranks = []
        for i in range(len(arr_request_msg)):
            if len(arr_request_msg[i]) != 0:
                req_msg = arr_request_msg[i][0]
                if req_msg.info == 'steal_request' and req_msg.recv_time == clock:
                    list_idle_ranks.append(i)

        # check busy ranks available
        list_busy_ranks = []
        for i in range(len(busy_queues)):
            busy_rank = busy_queues[i][0]
            list_busy_ranks.append(busy_rank)

        # check all pairs of idle and busy ranks
        while len(list_busy_ranks) != 0 and len(list_idle_ranks) != 0:

            # random choose a busy candidate
            busy_candidate = random.choice(list_busy_ranks)
            busy_candidate_queue_size = busy_queues[busy_candidate][1]

            # exchange request and accept messages
            if len(list_idle_ranks) != 0 and busy_candidate_queue_size >= MIN_TASKS_IN_QUEUE_FOR_STEAL:
                idle_candidate = random.choice(list_idle_ranks)
                checkout_req_msg = arr_request_msg[idle_candidate][0]
                if checkout_req_msg.info == 'accepted':
                    accept_rank = checkout_req_msg.accept_rank
                    checkout_ack_msg = arr_accept_msg[accept_rank][0]
                    arrival_time = checkout_ack_msg.recv_time
                    if arrival_time < clock:
                        if accept_rank != busy_candidate:
                            # new accept for the current busy candidate
                            new_accept_msg = Message(busy_candidate, idle_candidate, 'steal_accept')
                            new_accept_msg.set_time(clock, clock+LATENCY)
                            arr_accept_msg[busy_candidate].append(new_accept_msg)
                            # removed the expired accept for the old accept rankt
                            arr_accept_msg[accept_rank].pop(0)
                            print('[DEBUG] Clock {:5d}: R{:2d} CONFIRMS accept for R{:2d} (sent at {:5d}, will recv at {:5d})\n'.format(
                                clock, busy_candidate, idle_candidate, clock, clock+LATENCY))
                        else:
                            # only need to change the time
                            checkout_ack_msg.set_time(clock, clock+LATENCY)
                            print('[DEBUG] Clock {:5d}: R{:2d} CHANGES accept for R{:2d} (sent at {:5d}, will recv at {:5d})\n'.format(
                                clock, busy_candidate, idle_candidate, clock, clock+LATENCY))
                        
                        # remove the processed busy and idle candidates
                        list_idle_ranks.remove(idle_candidate)
                        list_busy_ranks.remove(busy_candidate)
                else:
                    # because not yet get accepted, we creat the 1st accept now
                    accept_msg = Message(busy_candidate, idle_candidate, 'steal_accept')
                    accept_msg.set_time(clock, clock+LATENCY)
                    arr_accept_msg[busy_candidate].append(accept_msg)
                    # change the status of request
                    checkout_req_msg.info = "accepted"
                    checkout_req_msg.set_accept_proc(busy_candidate)
                    print('[DEBUG] Clock {:5d}: R{:2d} CONFIRMS accept for R{:2d} (sent at {:5d}, will recv at {:5d})\n'.format(
                        clock, busy_candidate, idle_candidate, clock, clock+LATENCY))
                    
                    # remove the processed busy and idle candidates
                    list_idle_ranks.remove(idle_candidate)
                    list_busy_ranks.remove(busy_candidate)


def recv_steal_accept(clock, arr_queue_status, arr_request_msg, arr_accept_msg):

    # side of processes with EMPTY queue
    empty_queues = arr_queue_status[0]
    if len(empty_queues) != 0:

        # list for marking all accepted ranks per requested rank
        list_accepted_ranks = []
        for i in range(len(arr_request_msg)):
            list_accepted_ranks.append([])

        # list all available idle ranks
        list_idle_ranks = []
        for i in range(len(empty_queues)):
            idle_rank = empty_queues[i][0]
            list_idle_ranks.append(idle_rank)

        # list all available and accepted busy ranks, but we need 
        # to check the request messages not the accept messages
        list_busy_ranks = []
        for i in range(len(arr_accept_msg)):
            if len(arr_accept_msg[i]) != 0:

                checkout_accept_msg = arr_accept_msg[i][0]
                arrived_time = checkout_accept_msg.recv_time
                selected_idle_rank = checkout_accept_msg.receiver

                if clock < 19200:
                    print('Clock {:5d}: Idle R{:2d} acc_msg.info={}, acc_msg.arr={}, receiver={}'.format(clock, i, 
                                                        checkout_accept_msg.info, arrived_time, selected_idle_rank))
                
                if arrived_time == clock and selected_idle_rank in list_idle_ranks:
                    list_busy_ranks.append(i)
                    list_accepted_ranks[selected_idle_rank].append(i)
        
        # check one-by-one idle ranks
        for i in list_idle_ranks:
            if len(list_accepted_ranks[i]) != 0 and len(list_busy_ranks) != 0:
                busy_candidate = random.choice(list_accepted_ranks[i])
                # check the request and accept messages
                checkout_acc_msg = arr_accept_msg[busy_candidate][0]
                checkout_acc_msg.info = 'sending_task'
                checkout_req_msg = arr_request_msg[i][0]
                checkout_req_msg.info = 'stealing_task'
                checkout_req_msg.set_accept_proc(busy_candidate)
                print('[DEBUG] Clock {:5d}: R{:2d} will STEAL task from R{:2d}'.format(clock, i, busy_candidate))
                # remove the busy candidate from list_busy_ranks
                list_busy_ranks.remove(busy_candidate)


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