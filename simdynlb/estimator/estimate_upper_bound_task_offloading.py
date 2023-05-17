from queue import Queue
from time import sleep, perf_counter
from threading import Thread

import re
import os
import sys
import numpy as np
import pandas as pd

# -----------------------------------------------------
# Time counter/Delay time
# -----------------------------------------------------

# -----------------------------------------------------
# Init simulation
# -----------------------------------------------------
def init_simulation(cf):
    # storing arrays
    arr_given_tasks = []
    arr_execu_rates = []
    # extract config info
    num_processes = cf[0]
    num_total_tasks = cf[1]
    slowdown_scale = cf[2]
    num_sld_processes = cf[3]
    execute_rate = cf[5]
    num_tasks_per_rank = int(num_total_tasks/num_processes)
    # init queues of tasks
    for p in range(num_processes):
        arr_local_tasks = []
        ntasks = num_tasks_per_rank
        if p == num_processes-1:
            ntasks = num_total_tasks - ((num_processes-1) * num_tasks_per_rank)
        for i in range(ntasks):
            arr_local_tasks.append(1)
        arr_given_tasks.append(arr_local_tasks)
        # add execution rate to each process
        arr_execu_rates.append(execute_rate)
    # check slowdown
    for p in range(num_sld_processes):
        arr_execu_rates[p] = arr_execu_rates[p] * slowdown_scale
    # check results
    for i in range(num_processes):
        print('   + P{}: num_tasks={}, exe_rate={}'.format(i, len(arr_given_tasks[i]), arr_execu_rates[i]))
    # return
    return [arr_given_tasks, arr_execu_rates]

# -----------------------------------------------------
# Update load array
# -----------------------------------------------------

# -----------------------------------------------------
# Offload & Receive tasks
# -----------------------------------------------------

# -----------------------------------------------------
# Balancing stuff
# -----------------------------------------------------

# -----------------------------------------------------
# Simulation engine
# -----------------------------------------------------
def simulate_par_task_execution(arr_given_tasks, arr_exe_rates):
    # init clock and load info arrays
    clock = 0
    arr_local_load = []
    arr_remot_load = []
    arr_being_exe_tasks = []
    # check the queues in the first time
    num_procs = len(arr_exe_rates)
    queues_status = 0
    tasks_being_executed = 0.0
    for i in range(num_procs):
        queues_status += len(arr_given_tasks[i]) # get num. tasks on each proc
        arr_local_load.append(0)
        arr_remot_load.append(0)
        arr_being_exe_tasks.append(0)
    # main loop
    while(queues_status != 0 or tasks_being_executed != 0):
        # increase clock
        clock += 1
        # print('=============DEBUG(clk{:5d})=============='.format(clock))
        sum_remain_tasks = 0
        sum_being_exe_task = 0.0
        # pop task from the queues and execute them
        for i in range(num_procs):
            queue = arr_given_tasks[i]
            # check the being-executed tasks
            if arr_being_exe_tasks[i] != 0:
                cur_task = arr_being_exe_tasks[i]
                if cur_task > 1:
                    arr_being_exe_tasks[i] = cur_task-1
                    arr_local_load[i] += 1
                elif cur_task < 1:
                    # check the last tast
                    if len(queue) != 0:
                        new_task = queue.pop()
                        task_runtime = 1 / arr_exe_rates[i]
                        arr_being_exe_tasks[i] = task_runtime - (1-cur_task)
                        arr_local_load[i] += 1 # if not the last task
                        # print('   --> new_task={:5.2f}, cur_executing_task: {:5.2f}'.format(task_runtime, cur_task))
                    else:
                        new_task = 0
                        arr_being_exe_tasks[i] = 0.0
                        arr_local_load[i] += cur_task 
                else: # the case cur_task exe_time = 1
                    arr_being_exe_tasks[i] = 0.0
                    arr_local_load[i] += cur_task 
                
                # print('   [CLK{}] P[{}], arr_local_load={}, cur_task={}'.format(clock, i, arr_local_load[i], arr_being_exe_tasks[i]))

            # no tasks being executed, then ready for popping a new one
            else:
                exe_rate = arr_exe_rates[i]
                task_runtime = 1 / exe_rate
                tmp_load = 0.0
                # check how many tasks can be executed in a clock
                if len(queue) != 0:
                    if exe_rate > 1.0:
                        ntasks = int(exe_rate)
                        for i in range(ntasks):
                            task = queue.pop()
                            arr_local_load[i] += task_runtime
                            tmp_load += task_runtime

                    new_task = queue.pop()
                    arr_being_exe_tasks[i] = task_runtime - (1 - tmp_load)
                    arr_local_load[i] += 1
                # print('   [CLK{}] P[{}], arr_local_load={}, cur_task={}'.format(clock, i, arr_local_load[i], arr_being_exe_tasks[i]))

            # count remaining tasks
            sum_remain_tasks += len(arr_given_tasks[i])
            sum_being_exe_task += arr_being_exe_tasks[i]
        
            # debug info clock by clock
            # print('   P[{}]: local_load={:5.2f}, queue_status={}'.format(i, arr_local_load[i], len(arr_given_tasks[i])))

        # update queue status
        queues_status = sum_remain_tasks
        tasks_being_executed = sum_being_exe_task

        # limit clock for debugging
        # if clock == 20:
        #     exit(1)

    # return simulated results
    return [arr_local_load, arr_remot_load]

# -----------------------------------------------------
# Util functions
# -----------------------------------------------------
def read_setup(fn):
    file = open(fn, 'r')
    lines = file.readlines()
    cf_num_processes = 0
    cf_num_tasks = 0
    cf_slowdown = 0.0
    cf_num_slowdown_processes = 0
    cf_bandwidth = 0.0
    cf_exe_rate = 0.0
    for l in lines:
        if "num_process" in l:
            cf_num_processes = int(l.split(' ')[1])
        elif "num_tasks" in l:
            cf_num_tasks = int(l.split(' ')[1])
        elif "slowdown" in l:
            cf_slowdown = float(l.split(' ')[1])
        elif "num_sld_processes" in l:
            cf_num_slowdown_processes = int(l.split(' ')[1])
        elif "bandwidth" in l:
            cf_bandwidth = float(l.split(' ')[1])
        elif "exe_rate" in l:
            cf_exe_rate = float(l.split(' ')[1])
        
    cf_array = [cf_num_processes, cf_num_tasks,
                cf_slowdown, cf_num_slowdown_processes,
                cf_bandwidth, cf_exe_rate]
    return cf_array

def read_latency_bw_data(folder):
    sub_folders = os.listdir(folder)
    systems = []
    sizes = []
    latencies = []
    bw = []
    for sf in sub_folders:
        subsubfolder = os.path.join(folder, sf)
        files = os.listdir(subsubfolder)
        for f in files:
            if 'latency' in f:
                opened_file = open(os.path.join(subsubfolder, f), 'r')
                print('File: {}'.format(opened_file.name))
                lines = opened_file.readlines()
                for idx, l in enumerate(lines):
                    lcontent = l.strip('\n')
                    # print('Line {}: {}'.format(idx, lcontent))
                    if idx >= 3:
                        lnumbers = re.findall(r'\d+.?\d', lcontent)
                        sys = sf
                        s_val = float(lnumbers[0])
                        l_val = float(lnumbers[1])
                        # print('Line {}: {}'.format(idx, lnumbers))
                        systems.append(sys)
                        sizes.append(s_val)
                        latencies.append(l_val)
            if 'bw' in f:
                opened_file = open(os.path.join(subsubfolder, f), 'r')
                print('File: {}'.format(opened_file.name))
                lines = opened_file.readlines()
                for idx, l in enumerate(lines):
                    lcontent = l.strip('\n')
                    # print('Line {}: {}'.format(idx, lcontent))
                    if idx >= 3:
                        lnumbers = re.findall(r'\d+.?\d', lcontent)
                        s_val = float(lnumbers[0])
                        b_val = float(lnumbers[1])
                        bw.append(b_val)
                        # print('Line {}: {}'.format(idx, lnumbers))
    # generate dataframe with pandas
    data = []
    for i in range(len(systems)):
        row = [systems[i], sizes[i], latencies[i], bw[i]]
        data.append(row)
    df = pd.DataFrame(data, columns =['system', 'size(bytes)', 'latency(us)', 'bw(MB/s)'])
    # file_out = './latency_bw_data.csv'
    # df.to_csv(file_out, index=False)
    # return dataframe
    return df

# -----------------------------------------------------
# Main simulation engine
# -----------------------------------------------------
if __name__ == "__main__":

    # read input configuration
    if len(sys.argv) < 2:
        print('Usage: python estimate_upp... <imb_input> <lat_bw_dat_folder> [bound_mode]')
        print('\t+ Mode 0: upper bound with avarage load difference (default)')
        print('\t+ Mode 1: upper bound with min-max load difference')
        exit(1)
    filename = sys.argv[1]
    configs = read_setup(filename)
    # check setup configuration
    print('-------------------------------------------')
    print('Configuration:')
    print('   + num. processes: {:5d}'.format(configs[0]))
    print('   + num. tasks:     {:5d}'.format(configs[1]))
    print('   + slowdown:       {:5.1f}'.format(configs[2]))
    print('   + num. sld.procs: {:5d}'.format(configs[3]))
    print('   + bandwidth:      {:5.1f} (MB/s)'.format(configs[4]))
    print('   + exe_rate:       {:5.1f} (task/s)'.format(configs[5]))

    # check the data folder of latencies and bandwidths
    lat_bw_data_folder = sys.argv[2]

    # check mode for calculating the upper bound of K
    bound_mode = 0
    if sys.argv[3] != None:
        bound = int(sys.argv[3])
        if bound == 1:
            bound_mode = 1

    # initialize the configuration
    print('-------------------------------------------')
    print('Init Config:')
    init_res = init_simulation(configs)
    ARR_GIVEN_TASKS = init_res[0]
    ARR_EXECU_RATES = init_res[1]
    # for i in range(len(ARR_EXECU_RATES)):
    #     print('   P{}: {}'.format(i, ARR_GIVEN_TASKS[i]))

    # simulate task execution
    simu_res = simulate_par_task_execution(ARR_GIVEN_TASKS, ARR_EXECU_RATES)
    ARR_LOCAL_LOAD = simu_res[0]
    ARR_REMOT_LOAD = simu_res[1]
    print('-------------------------------------------')
    print('Simulation results:')
    num_procs = len(ARR_EXECU_RATES)
    for i in range(num_procs):
        print('   + P[{:3d}]: local_load={:7.1f}, remot_load={:7.1f}'.format(i, ARR_LOCAL_LOAD[i], ARR_REMOT_LOAD[i]))

    # statistic the simulation results
    print('-------------------------------------------')
    print('Statistic:')
    max_load = np.max(ARR_LOCAL_LOAD)
    min_load = np.min(ARR_LOCAL_LOAD)
    avg_load = np.average(ARR_LOCAL_LOAD)
    R_imb = max_load / avg_load - 1
    sum_overloaded_load = 0
    sum_underloaded_load = 0
    for i in range(num_procs):
        load = ARR_LOCAL_LOAD[i]
        if load > avg_load:
            sum_overloaded_load += load - avg_load
        elif load < avg_load:
            sum_underloaded_load += avg_load - load
    print('max. load: {:7.1f}'.format(max_load))
    print('min. load: {:7.1f}'.format(min_load))
    print('avg. load: {:7.1f}'.format(avg_load))
    print('R_imb:     {:7.1f}'.format(R_imb))
    print('sum. overloaded_load:  {:7.1f}'.format(sum_overloaded_load))
    print('sum. underloaded_load: {:7.1f}'.format(sum_underloaded_load))

    # get latency and bw data
    print('-------------------------------------------')
    print('Latency and Bandwidth Data:')
    lat_bw_df = read_latency_bw_data(lat_bw_data_folder)

    # estimate the upper bound of K tasks by offloading
    print('-------------------------------------------')
    print('Estimate K:')
    # corresponding matrix size: 128, 256, 512, 1024, 1280, 1536, 1792
    matr_size = [128, 256, 512, 1024, 1280, 1536, 1792]
    task_size = [0.39, 1.57, 6.29, 25.16, 39.32, 56.62, 77.07]
    corr_size_in_osu_benchmark = [524288.0, 2097152.0, 8388608.0, 33554432.0, 67108864.0, 134217728.0, 134217728.0]
    for i in task_size:
        print('{:12.2f}(MB) --> {:12.2f}(bytes)'.format(i, i*1024*1024))
    
    # extract dataset from each system
    coolmuc_data = lat_bw_df[lat_bw_df['system']=='coolmuc2']
    sng_data = lat_bw_df[lat_bw_df['system']=='sng']
    beast_data = lat_bw_df[lat_bw_df['system']=='beast']
    
    # calculate K and create a new dataframe
    data_lat_bw_K = []
    system_labels = ['coolmuc2', 'sng', 'beast']
    for idx, sys in enumerate([coolmuc_data, sng_data, beast_data]):
        for i,s in enumerate(task_size):
            sys_name = system_labels[idx]
            sys_data = sys
            cor_row = sys[sys['size(bytes)'] == corr_size_in_osu_benchmark[i]]
            cor_lat = cor_row.values[0][2]
            cor_bw  = cor_row.values[0][3]
            # print('   {}: task_size={}, cor_size={}, cor_lat={}, cor_bw={}'.format(sys_name, s, corr_size_in_osu_benchmark[i], cor_lat, cor_bw))
            # merge with inputs from imb case
            P = configs[0]
            P_under = configs[3]
            P_over = P - configs[3]
            l = cor_lat/pow(10,6)   # latency corresponding to task size
            B = cor_bw              # bandwidth corresponding to task size
            d = (l + s/B) * pow(10,3)   # delay corresponding to task size

            # estimate K values
            if bound_mode == 0:
                K = sum_overloaded_load / (P_under * (l + s/B))
            else:
                K = (max_load - min_load) / (2 * (l + s/B))

            # generate data frame with K
            df_row = [sys_name, matr_size[i], s, corr_size_in_osu_benchmark[i], cor_lat, cor_bw, d, int(K)]
            data_lat_bw_K.append(df_row)

    df_lat_bw_K = pd.DataFrame(data_lat_bw_K, columns =['system', 'mat_size', 'task_size(MB)', 'corrsize_in_os(bytes)', 'latency(us)', 'bw(MB/s)', 'd(ms)', 'K'])

    # write to file
    example = filename.split('_')[0]
    bound_label = 'avg_bound'
    if bound_mode == 1:
        bound_label = 'minmax_bound'
    file_out = './' + example + '_' + bound_label + '_latency_bw_K_data.csv'
    df_lat_bw_K.to_csv(file_out, index=False)