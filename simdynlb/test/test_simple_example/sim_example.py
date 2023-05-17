from queue import Queue
import sys
from tkinter import OFF
import numpy as np

from time import sleep, perf_counter
from threading import Thread

# -----------------------------------------------------
# Time counter/Delay time
# -----------------------------------------------------
MAX_DURATION = 1000 # ms, ns, or time unit
MIN_REL_LOAD_IMBALANCE = 0.05
PERCENT_DIFF_TASKS_TO_OFFLOAD = 0.05
THROUGHPUT = 1 # denotes 1 task/time unit
TIMECLOCK = 0
LATENCY = 2
DELAY = 2
tcount = 0

# -----------------------------------------------------
# Total load recoder
# -----------------------------------------------------
GIVEN_TASK_ARR = [80, 10, 5, 5, 5, 5, 9, 9]
LOCAL_LOAD_ARR = [0, 0, 0, 0, 0, 0, 0, 0]
REMOT_LOAD_ARR = [0, 0, 0, 0, 0, 0, 0, 0]
TDONE_RECO_ARR = [0, 0, 0, 0, 0, 0, 0, 0]

# -----------------------------------------------------
# Offloading and task queues
# -----------------------------------------------------
OFFLOAD_TRACK_ARR = []
LOCAL_TASK_QUEUE = []
REMOT_TASK_QUEUE = []

# -----------------------------------------------------
# Update load array
# -----------------------------------------------------
def update_load(r):
  # if remot_task_queue has some tasks | priority 1
  if REMOT_TASK_QUEUE[r].qsize() > 0:
    remot_task_load = REMOT_TASK_QUEUE[r].get() # get a remote task
    REMOT_LOAD_ARR[r] += 1 # remot_task_load # increase the remote load
  else:
    local_task_load = LOCAL_TASK_QUEUE[r].get() # get a local task
    LOCAL_LOAD_ARR[r] += 1 # local_task_load # increase the local load

# -----------------------------------------------------
# Offload & Receive tasks
# -----------------------------------------------------
def offload_tasks(src, des, ntasks, toffload, tarrive):
  # dequeue tasks from src
  offloaded_task = LOCAL_TASK_QUEUE[src].get()
  # set task info 
  migratabl_task = (offloaded_task, src, des, toffload, tarrive)
  # enqueue tasks to the communication queue
  OFFLOAD_TRACK_ARR[des].put(migratabl_task)
  print("[Offload] OFFLOAD_TRACK_ARR[R{}], migratabl_task={}".format(des, migratabl_task))

def receive_tasks(OFFLOAD_TRACK_ARR, timestamp):
  num_ranks = len(GIVEN_TASK_ARR)
  for i in range(num_ranks):
    # print("[Debug] OFFLOAD_TRACK_ARR[R{}].qsize() = {}".format(i, OFFLOAD_TRACK_ARR[i].qsize()))
    if OFFLOAD_TRACK_ARR[i].qsize() > 0:
      remote_task = OFFLOAD_TRACK_ARR[i].get()
      src = remote_task[1]
      des = remote_task[2]
      toffloa = remote_task[3]
      tarrive = remote_task[4]
      print("[Debug] Offloaded-Task from R{} to R{}: toffload={}, tarrive={}".format(src, des, toffloa, tarrive))
      if tarrive == timestamp:
        # update remote task queue
        REMOT_TASK_QUEUE[i].put(remote_task[0])
        print("[Receiv] REMOT_TASK_QUEUE[R{}], remote_task={}".format(i, remote_task))

# -----------------------------------------------------
# Balancing stuff
# -----------------------------------------------------
def balancing(tcount):
  # check local queue status
  num_ranks = len(GIVEN_TASK_ARR)
  QUEUE_SIZE_STATUS_ARR = np.zeros(num_ranks)
  for r in range(num_ranks):
    QUEUE_SIZE_STATUS_ARR[r] = LOCAL_TASK_QUEUE[r].qsize()

  # sort the queues by the current size status
  sortLCQ = np.argsort(QUEUE_SIZE_STATUS_ARR)
  
  # show the status
  str_rank_orders = '[ '
  for i in range(len(sortLCQ)):
    str_rank_orders += 'R' + str(sortLCQ[i]) + ' '
  str_rank_orders += ']'
  
  str_load_orders = '[ '
  for i in range(len(sortLCQ)):
    idx = sortLCQ[i]
    str_load_orders += str(LOCAL_TASK_QUEUE[idx].qsize()) + ' '
  str_load_orders += ']'

  # check the imb
  lmax = QUEUE_SIZE_STATUS_ARR[sortLCQ[-1]]
  lmin = QUEUE_SIZE_STATUS_ARR[sortLCQ[0]]
  lavg = np.average(QUEUE_SIZE_STATUS_ARR)
  rimb = 0.0
  rimb_min_max = 0.0
  if lavg != 0 and lmax != 0:
    rimb = lmax/lavg - 1
    rimb_min_max = (lmax - lmin) / lmax

  # print the status
  if rimb >= MIN_REL_LOAD_IMBALANCE:
    print(str_rank_orders + ' = ' + str_load_orders + ' | Imb. = ' + str(rimb))
    print('Ratio (max, min): {}'.format(rimb_min_max))

    # calculate tasks to offload
    OFFLOAD_PAIR_RANKS = []
    for i in range(num_ranks):
      src_ntasks = [-1,-1]
      OFFLOAD_PAIR_RANKS.append(src_ntasks)

    for i in range(int(num_ranks/2), num_ranks):
      # check the number of tasks in src. rank
      cur_qsize = LOCAL_TASK_QUEUE[sortLCQ[i]].qsize()
      if cur_qsize > 2:
        OFFLOAD_PAIR_RANKS[i][0] = sortLCQ[i] # src. rank
        OFFLOAD_PAIR_RANKS[i][1] = sortLCQ[num_ranks - i - 1] # des. rank
        print("[Debug] src_rank={}, des_rank={}...".format(OFFLOAD_PAIR_RANKS[i][0], OFFLOAD_PAIR_RANKS[i][1]))

    # offload tasks
    for i in range(num_ranks):
      if np.sum(OFFLOAD_PAIR_RANKS[i]) > 0:
        src_rank = OFFLOAD_PAIR_RANKS[i][0]
        des_rank = OFFLOAD_PAIR_RANKS[i][1]
        ntasks2offload = 1
        t_offloa = tcount
        t_arrive = tcount + int(ntasks2offload/THROUGHPUT)
        print("[Offload] R{} ---> R{}: {} task, send at t{}, recv at t{}".format(src_rank, des_rank, ntasks2offload, t_offloa, t_arrive))
        offload_tasks(src_rank, des_rank, ntasks2offload, t_offloa, t_arrive)

# -----------------------------------------------------
# Init offloading tracker array
# -----------------------------------------------------
for i in range(len(GIVEN_TASK_ARR)):
  OFFLOAD_TRACK_ARR.append(Queue())
  LOCAL_TASK_QUEUE.append(Queue())
  REMOT_TASK_QUEUE.append(Queue())

for r in range(len(GIVEN_TASK_ARR)):
  num_given_tasks = GIVEN_TASK_ARR[r]
  for i in range(num_given_tasks):
    LOCAL_TASK_QUEUE[r].put(i)

# for r in range(len(GIVEN_TASK_ARR)):
#   print('R{}: qsize = {}'.format(r, LOCAL_TASK_QUEUE[r].qsize()))

# -----------------------------------------------------
# Main simulation engine
# -----------------------------------------------------
_stat_all_queue_empty = False

while _stat_all_queue_empty == False:

  # increase time clock
  tcount = tcount + 1

  # check and recieve offload tasks
  receive_tasks(OFFLOAD_TRACK_ARR, tcount)

  # check all queue status
  _sum_queue_size = 0
  for r in range(len(GIVEN_TASK_ARR)):
    _sum_queue_size += LOCAL_TASK_QUEUE[r].qsize()
  if _sum_queue_size == 0:
    _stat_all_queue_empty = True
    print('------------------------------------------------')
    print('timestep {}: Last state'.format(tcount))
    print('------------------------------------------------')
  else:
    print('------------------------------------------------')
    print('timestep {}: _sum_queue_size = {}'.format(tcount, _sum_queue_size))

  # dynamic balancing
  balancing(tcount)

  # decrease load/proces as parallel processing
  num_ranks = len(GIVEN_TASK_ARR)
  for r in range(num_ranks):
    qstatus = LOCAL_TASK_QUEUE[r].qsize() + REMOT_TASK_QUEUE[r].qsize()

    # update load and task done
    if qstatus > 0:
      update_load(r)
    elif qstatus == 0 and TDONE_RECO_ARR[r] == 0:
      TDONE_RECO_ARR[r] = tcount - 1

  # print('{}, tcount = {}'.format(LOCAL_TASK_QUEUE, tcount))

# -----------------------------------------------------
# Status checker
# -----------------------------------------------------
for r in range(num_ranks):
  print('------------------------------------------------')
  print('R{} done at time {}'.format(r, TDONE_RECO_ARR[r]))

# -----------------------------------------------------
# Performance statistic
# -----------------------------------------------------
Lmax = np.max(TDONE_RECO_ARR)
Lmin = np.min(TDONE_RECO_ARR)
Lavg = np.average(TDONE_RECO_ARR)
Rimb = Lmax/Lavg - 1

print('------------------------------------------------')
print('Lmax: {:7.2f}'.format(Lmax))
print('Lmin: {:7.2f}'.format(Lmin))
print('Lavg: {:7.2f}'.format(Lavg))
print('Rimb: {:7.2f}'.format(Rimb))
print('------------------------------------------------')

  