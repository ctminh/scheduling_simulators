import numpy as np
import random

from task import *

"""
Offloading interface for migrating tasks from slow process to faster ones
    - run on a separate thread
    - bases on the result of balancers
    - take migrating tasks plus with Delay + Overhead(balancingcompute)
"""

# -----------------------------------------------------
# Constant Definition
# -----------------------------------------------------
OVERHEAD_BALANCING_OPS = 1.0 # in miliseconds
OVERHEAD_DELAY = 1.0 # in miliseconds
CLOCK_RATE = 1E3 # count as miliseconds
NOISE = 0.15 # additional noise in task runtime when it is migrated

# -----------------------------------------------------
# Util Functions
# -----------------------------------------------------
def randomize_cost(iter, cost_val, noise):
    random.seed(iter)
    # check noise value
    if noise > cost_val:
        noise = cost_val
    min = cost_val - noise
    max = cost_val + noise
    res = random.randint(min, max)
    return res

def estimate_new_task_runtime(old_dur, sld_processes, sld_scales, origin_node, new_node, iter, clock_rate):
    
    # assume the task runtime is the same if remote node is not the slowdown one
    new_dur = old_dur

    # if the remote node is the slowdown one
    for i in range(len(sld_processes)):
        tmp_proc = sld_processes[i]
        tmp_scal = sld_scales[i]
        if origin_node == tmp_proc and new_node != tmp_proc:
            new_dur = randomize_cost(iter, old_dur/2, old_dur/4)
        elif origin_node != tmp_proc and new_node == tmp_proc:
            dur = 1.0 / tmp_scal
            dur = dur * clock_rate
            new_dur = dur

    return new_dur

# -----------------------------------------------------
# Offload Functions
# -----------------------------------------------------
def select_tasks_to_offload(clock, local_queues, arr_victim_offloader, 
                            iter, cost_balancing, cost_migration_delay, noise):
    
    num_procs = len(arr_victim_offloader)

    for i in range(num_procs):
        num_tasks_for_migrating = len(arr_victim_offloader[i])
        if num_tasks_for_migrating > 0:
            # proceed the first pair
            pair_off_vic = arr_victim_offloader[i].pop(0)
            off_rank = pair_off_vic[0]
            vic_rank = pair_off_vic[1]
            assert(i == off_rank)
            queue_length_offloader = len(local_queues[i])
            queue_length_victim = len(local_queues[vic_rank])
            diff_load = abs(queue_length_offloader - queue_length_victim)
        
            # choose the last task which is going to be offloaded
            if queue_length_offloader > 2 and diff_load > 2:
                for j in range(queue_length_offloader-1, 2, -1):
                    task2offload = local_queues[i][j]
                    remote_node  = task2offload.remot_node
                    if remote_node == -1:
                        # set remote node
                        task2offload.set_remote_node(vic_rank)
                        # set migrate time
                        migrate_time = clock + randomize_cost(iter, cost_balancing, noise)
                        task2offload.set_mig_time(migrate_time)
                        # set arrive time
                        arrive_time = migrate_time + randomize_cost(iter, cost_migration_delay, noise)
                        task2offload.set_arr_time(arrive_time)
                        # check
                        # print("[Tcomm] clock[{}]: (select_tasks) R{}-victim R{}, diff={}".format(clock, off_rank, vic_rank, diff_load))
                        break

def steal_tasks(clock, local_queues, arr_queue_status, arr_steal_request_msg, arr_steal_accept_msg, 
                iter, cost_migration_delay, sld_processes, sld_scales, clock_rate, noise):
    
    # check the processes with empty queues
    empty_queues = arr_queue_status[0]
    busy_queues  = arr_queue_status[1]
    if len(empty_queues) != 0:
        for i in range(len(empty_queues)):
            idle_rank = empty_queues[i][0]
            checkout_request_msg = arr_steal_request_msg[idle_rank][0]
            req_status = checkout_request_msg.info
            if req_status == 'stealing_task':
                req_rank_for_stealing = checkout_request_msg.receiver
                if len(busy_queues) != 0:
                    checkout_accept_msg = arr_steal_accept_msg[req_rank_for_stealing][0]
                    ack_status = checkout_accept_msg.info
                    ack_idle_rank = checkout_accept_msg.receiver
                    if ack_status == 'sending_task' and idle_rank == ack_idle_rank:
                        # print('[DEBUG] Clock {:5d}: R{:2d} is idle | stealing task from R{:2d}'.format(clock, idle_rank, req_rank_for_stealing))
                        # mark a task from the busy rank for stealing
                        if len(local_queues[req_rank_for_stealing]) > 2:
                            for j in range(len(local_queues[req_rank_for_stealing])-1, 2, -1):
                                task2steal = local_queues[req_rank_for_stealing][j] # last task
                                remote_node = task2steal.remot_node
                                if remote_node == -1: # mark a new task for stealing
                                    task2steal.set_remote_node(idle_rank)
                                    task2steal.set_mig_time(clock)
                                    arrive_time = clock + randomize_cost(iter, cost_migration_delay, noise)
                                    task2steal.set_arr_time(arrive_time)
                                    break
                                else: # check the marked task is arrived or not yet
                                    if remote_node == idle_rank and task2steal.arr_time == clock:
                                        stolen_task = local_queues[req_rank_for_stealing].pop()
                                        # update some new info
                                        old_node = stolen_task.local_node
                                        old_dur = stolen_task.get_dur()
                                        new_dur = estimate_new_task_runtime(old_dur, sld_processes, sld_scales, old_node, i, iter, clock_rate)
                                        stolen_task.dur = new_dur
                                        # add this task to the remote side
                                        local_queues[idle_rank].append(stolen_task)
                                        # remove the messages of request and accept
                                        arr_steal_request_msg[idle_rank].pop()
                                        arr_steal_accept_msg[req_rank_for_stealing].pop()
                                        

def offload_tasks(clock, local_queues, remote_queues, arr_tmp_buffer_migrated_tasks, 
                    sld_processes, sld_scales, iter, clock_rate, noise):
    
    num_procs = len(arr_tmp_buffer_migrated_tasks)
    # ------------------------------------------------------
    # proceed for sending tasks over the network
    # ------------------------------------------------------
    for i in range(num_procs):
        num_remain_tasks = len(local_queues[i])
        if num_remain_tasks > 2:
            # check the tasks at rear
            tmp_offload = local_queues[i][-1] # choose the task at rear in the queue
            victim = tmp_offload.remot_node
            if victim != -1:
                # check the clock and migrate_time
                if tmp_offload.mig_time == clock:
                    # print("[Tcomm] clock[{}]: (offload_tasks) R{} to victim R{}".format(clock, i, victim))
                    # pop the task
                    tmp_offload = None
                    task2migrate = local_queues[i].pop()
                    # add task to the migrate buffer over network
                    arr_tmp_buffer_migrated_tasks[victim].append(task2migrate)
    # ------------------------------------------------------
    # proceed for receiving tasks over the network
    # ------------------------------------------------------
    for i in range(num_procs):
        num_tasks_being_migrated = len(arr_tmp_buffer_migrated_tasks[i])
        if num_tasks_being_migrated > 0:
            tmp_receive = arr_tmp_buffer_migrated_tasks[i][0] # choose the task at front in the buffer
            arrive_time = tmp_receive.arr_time
            if arrive_time == clock:
                # pop the task
                tmp_receive = None
                task2receive = arr_tmp_buffer_migrated_tasks[i].pop(0)
                # varied the task runtime
                old_node = task2receive.local_node
                old_dur = task2receive.get_dur()
                new_dur = estimate_new_task_runtime(old_dur, sld_processes, sld_scales, old_node, i, iter, clock_rate)
                task2receive.dur = new_dur
                # add task to the remote queue at the victim side
                remote_queues[i].append(task2receive)
                # check migration
                # print("[Tcomm] clock[{}]: (receive_tasks) victim R{} from R{}, old_dur={}, new_dur={}".format(clock, i, old_node, old_dur, new_dur))
    return 0
        
