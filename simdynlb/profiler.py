import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import csv
import os

from migrator import *

"""
Profiling interfaces for tracking the task execution
    - plot gann charts
    - statistics about task/load execution
"""

# -----------------------------------------------------
# Util Functions
# -----------------------------------------------------
def show_num_executed_tasks(arr_executed_tasks):
    num_procs = len(arr_executed_tasks)
    print('--------------------')
    print('Profiling Info:     ')
    print('--------------------')
    ranks_arr = []
    num_local_tasks_arr = []
    num_remote_tasks_arr = []
    num_total_tasks_arr = []
    sum_total_tasks = 0
    for i in range(num_procs):
        ranks_arr.append('R' + str(i))
        num_tasks = arr_executed_tasks[i]
        num_local_tasks_arr.append(num_tasks[0])
        num_remote_tasks_arr.append(num_tasks[1])
        num_total_tasks_arr.append(num_tasks[0] + num_tasks[1])
        sum_total_tasks += num_tasks[0] + num_tasks[1]
    
    df_num_tasks = pd.DataFrame({
        'rank': ranks_arr,
        'num_local_tasks': num_local_tasks_arr,
        'num_remote_tasks': num_remote_tasks_arr,
        'num_total_tasks': num_total_tasks_arr
    })
    print(df_num_tasks)

def plot_gann_chart(gannt_local_tasks, gannt_remot_tasks):
    num_procs = len(gannt_local_tasks)

    # declare the chart
    fig, gnt = plt.subplots()

    # set labels for x- and y-axis
    gnt.set_xlabel('Time Progress')
    gnt.set_ylabel('Processes')

    # set x- or y-limits
    # gnt.set_xlim(0, max_ntasks*TIMESTEP_RATIO*1.0+TIMESTEP_RATIO*2)

    # set ticks on y-axis for showing the process-names
    ytick_values = [15]
    ytick_labels = ['P0']
    for i in range(1, num_procs):
        ytick_values.append(ytick_values[i-1] + 10)
        ytick_labels.append('P' + str(i))
    gnt.set_yticks(ytick_values)
    gnt.set_yticklabels(ytick_labels)

    # configure the graph attributes
    gnt.grid(True)

    # declare bars in schedule
    for r in range(num_procs):
        gnt.broken_barh(gannt_local_tasks[r], (10*r+10, 8), facecolors=('tab:green'), edgecolor='black')
    for r in range(num_procs):
        gnt.broken_barh(gannt_remot_tasks[r], (10*r+10, 8), facecolors=('tab:orange'), edgecolor='black')

    # display the chart
    # plt.show()

    # save to file
    O_balancing = int(OVERHEAD_BALANCING_OPS)
    O_delay = int(OVERHEAD_DELAY)
    fig_filename = "./visualized_OBalancing" + str(O_balancing) + "_ODelay" + str(O_delay) + ".pdf"
    plt.savefig(os.path.join("./", fig_filename), bbox_inches='tight')

# -----------------------------------------------------
# Visualize task exections
# -----------------------------------------------------
def visualize_task_execution(profiled_tasks_arr):
    num_procs = len(profiled_tasks_arr)
    gannt_values_local_tasks = []
    gannt_values_remot_tasks = []
    num_local_remote_tasks = []
    for i in range(num_procs):
        gannt_values_local_tasks.append([])
        gannt_values_remot_tasks.append([])
        num_local_remote_tasks.append([0, 0])

    for i in range(num_procs):
        # check process by process
        profiled_tasks_queue = profiled_tasks_arr[i]
        num_local_tasks = 0
        num_remot_tasks = 0
        num_total_executed_tasks = len(profiled_tasks_queue)
        for j in range(num_total_executed_tasks):
            # extract task information
            task = profiled_tasks_queue[j]
            task_id = task.tid
            exe_time = task.dur
            sta_time = task.sta_time
            end_time = task.end_time
            mig_time = task.mig_time
            loc_node = task.local_node
            rem_node = task.remot_node

            # simplify info for the gannt chart
            gann_info = (sta_time, end_time-sta_time)
    
            # track the number of local and remote tasks
            if loc_node != i and rem_node != -1 and rem_node != loc_node:
                num_remot_tasks += 1
                gannt_values_remot_tasks[i].append(gann_info)
            else:
                num_local_tasks += 1
                gannt_values_local_tasks[i].append(gann_info)

        # summarize the values
        num_local_remote_tasks[i][0] = num_local_tasks
        num_local_remote_tasks[i][1] = num_remot_tasks
    
    # show the summarized info of executed tasks
    show_num_executed_tasks(num_local_remote_tasks)

    # plot gannt-chart
    plot_gann_chart(gannt_values_local_tasks, gannt_values_remot_tasks)


# -----------------------------------------------------
# Profile the queue status
# -----------------------------------------------------
def profile_queue_status(arr_queue_status):
    num_procs = len(arr_queue_status)
    O_balancing = int(OVERHEAD_BALANCING_OPS)
    O_delay = int(OVERHEAD_DELAY)
    
    # write to file
    filename = './profiled_queues_obalancing' + str(O_balancing) + '_odelay' + str(O_delay) + '.csv'
    print('\tWrite profiled queue data to: {}'.format(filename))
    f = open(filename, 'w')
    writer = csv.writer(f)
    for i in range(num_procs):
        queue_stat = arr_queue_status[i]
        writer.writerow(queue_stat)
    f.close()


# -----------------------------------------------------
# Statistic info after execution
# -----------------------------------------------------
def statistic_info(arr_local_load, arr_remote_load, clockrate):
    ARR_LOCAL_LOAD = []
    ARR_REMOT_LOAD = []
    ARR_TOTAL_LOAD = []
    ARR_RANKS = []
    num_procs = len(arr_local_load)
    for i in range(num_procs):
        local_val = arr_local_load[i]/clockrate
        remot_val = arr_remote_load[i]/clockrate

        ARR_RANKS.append('R' + str(i))
        ARR_LOCAL_LOAD.append(local_val)
        ARR_REMOT_LOAD.append(remot_val)
        ARR_TOTAL_LOAD.append(local_val+remot_val)

    # create pandas dataframe
    df_load_info = pd.DataFrame({
        'rank': ARR_RANKS,
        'local_load': ARR_LOCAL_LOAD,
        'remote_load': ARR_REMOT_LOAD,
        'total_load': ARR_TOTAL_LOAD
    })
    print('--------------------')
    print('Statistic Info:')
    print('--------------------')
    print(df_load_info)

    # statistic the simulation results
    print('--------------------')
    print('Imbalance:')
    max_load = df_load_info['total_load'].max()
    min_load = df_load_info['total_load'].min()
    avg_load = df_load_info['total_load'].mean()
    R_imb = 0.0
    if avg_load != 0:
        R_imb = max_load / avg_load - 1
    print('max. load: {:7.1f}'.format(max_load))
    print('min. load: {:7.1f}'.format(min_load))
    print('avg. load: {:7.1f}'.format(avg_load))
    print('R_imb:     {:7.1f}'.format(R_imb))
    print('--------------------\n')