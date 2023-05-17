from matplotlib.ticker import EngFormatter

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import matplotlib.ticker as tck
import numpy as np
import pandas as pd
import imageio
import sys
import os
import csv
import re

# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

# ---------------------------------------------------------
# Util functions
# ---------------------------------------------------------
def k_milliseconds(x, pos):
    """The two arguments are the value and tick position."""
    return "{:d}k".format(int(x/1000))

"""Read the queue status results
"""
def read_queue_status_results(file):
    df = pd.read_csv(file, header=None)
    num_procs = df.shape[0]
    queue_status_arr = []
    for i in range(num_procs):
        row_data = df.iloc[i].to_numpy()
        queue_status_arr.append(row_data)
    return queue_status_arr

"""Plot the chart
"""
def plot_queue_status(queue_dataset, mode, token):
    # extract data
    ax1_data = queue_dataset[0]
    ax2_data = queue_dataset[1]
    ax3_data = queue_dataset[2]
    ax4_data = queue_dataset[3]
    ax5_data = queue_dataset[4]

    num_procs = len(queue_dataset[0])

    # create figure and axis objects with subplots()
    # set the size, 15 is width, 4 is height
    gs = gridspec.GridSpec(1,5)
    fig = plt.figure(figsize=(16,4))
    ax1 = plt.subplot(gs[0,0])
    ax2 = plt.subplot(gs[0,1])
    ax3 = plt.subplot(gs[0,2])
    ax4 = plt.subplot(gs[0,3])
    ax5 = plt.subplot(gs[0,4])

    # share x, y
    # ax1.sharex(ax4)
    # ax2.sharex(ax5)
    # ax3.sharex(ax6)
    xlimit = 600000

    # ---------------------------------------------------------
    # Line styles
    # ---------------------------------------------------------
    # lcolors = ['black', 'blue', 'darkgreen', 'red', 'darkorange', 'purple', 'teal', '#d5b60a']
    lcolors = ['#b2182b', '#4d4d4d', '#1b7837', '#9970ab', '#fdae61', '#74add1', '#8c510a', '#e6f598']
    
    legend_size = 8
    legend_labels = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']

    # formatter = EngFormatter()
    formatter = k_milliseconds
    o_bal = [0.1, 0.2, 0.5, 1.0, 2.0]
    o_del = [0.1, 0.2, 0.5, 1.0, 2.0]
    value = token/1000 * 100
    if mode == 'delay':
        for i in range(len(o_bal)):
            o_bal[i] = value
    elif mode == 'balancing':
        for i in range(len(o_bal)):
            o_del[i] = value

    # ---------------------------------------------------------
    # 1. Case 1
    # ---------------------------------------------------------
    ax1.set_title(r'$O_{balancing}='+ str(o_bal[0]) + r'\%, d=' + str(o_del[0]) + r'\%$')
    ax1_indices = np.arange(len(ax1_data[0]))
    for i in range(num_procs): # loop through the methods
        ax1.plot(ax1_indices, ax1_data[i], label=legend_labels[i], color=lcolors[i])
    ax1.set_ylabel("Queue length")
    ax1.set_xlabel("Time (ms)")
    ax1.set_xlim(0, xlimit)
    ax1.get_xaxis().set_major_formatter(formatter)
    ax1.legend(fontsize=legend_size)
    ax1.grid()

    # ---------------------------------------------------------
    # 2. Case 2
    # ---------------------------------------------------------
    ax2.set_title(r'$O_{balancing}='+ str(o_bal[1]) + r'\%, d=' + str(o_del[1]) + r'\%$')
    ax2_indices = np.arange(len(ax2_data[0]))
    for i in range(num_procs): # loop through the methods
        ax2.plot(ax2_indices, ax2_data[i], label=legend_labels[i], color=lcolors[i])
    # ax2.set_ylabel("Queue length")
    ax2.set_xlabel("Time (ms)")
    ax2.set_xlim(0, xlimit)
    ax2.get_xaxis().set_major_formatter(formatter)
    ax2.legend(fontsize=legend_size)
    ax2.grid()

    # ---------------------------------------------------------
    # 3. Case 3
    # ---------------------------------------------------------
    ax3.set_title(r'$O_{balancing}='+ str(o_bal[2]) + r'\%, d=' + str(o_del[2]) + r'\%$')
    ax3_indices = np.arange(len(ax3_data[0]))
    for i in range(num_procs): # loop through the methods
        ax3.plot(ax3_indices, ax3_data[i], label=legend_labels[i], color=lcolors[i])
    # ax3.set_ylabel("Queue length")
    ax3.set_xlabel("Time (ms)")
    ax3.set_xlim(0, xlimit)
    ax3.get_xaxis().set_major_formatter(formatter)
    ax3.legend(fontsize=legend_size)
    ax3.grid()
    
    # ---------------------------------------------------------
    # 4. Case 4
    # ---------------------------------------------------------
    ax4.set_title(r'$O_{balancing}='+ str(o_bal[3]) + r'\%, d=' + str(o_del[3]) + r'\%$')
    ax4_indices = np.arange(len(ax4_data[0]))
    for i in range(num_procs): # loop through the methods
        ax4.plot(ax4_indices, ax4_data[i], label=legend_labels[i], color=lcolors[i])
    # ax4.set_ylabel("Queue length")
    ax4.set_xlabel("Time (ms)")
    ax4.set_xlim(0, xlimit)
    ax4.get_xaxis().set_major_formatter(formatter)
    ax4.legend(fontsize=legend_size)
    ax4.grid()

    # ---------------------------------------------------------
    # 5. Case 5
    # ---------------------------------------------------------
    ax5.set_title(r'$O_{balancing}='+ str(o_bal[4]) + r'\%, d=' + str(o_del[4]) + r'\%$')
    ax5_indices = np.arange(len(ax5_data[0]))
    for i in range(num_procs): # loop through the methods
        ax5.plot(ax5_indices, ax5_data[i], label=legend_labels[i], color=lcolors[i])
    # ax5.set_ylabel("Queue length")
    ax5.set_xlabel("Time (ms)")
    ax5.set_xlim(0, xlimit)
    ax5.get_xaxis().set_major_formatter(formatter)
    ax5.legend(fontsize=legend_size)
    ax5.grid()
    

    # show the plot
    # plt.show()

    # save the figure
    posfix = ""
    if mode == "delay":
        posfix += "delay_impact_OB" + str(token)
    elif mode == "balancing":
        posfix += "blancing_impact_d" + str(token)

    fig_filename = "./queue_decrease_" + posfix + ".pdf"
    plt.savefig(os.path.join("./", fig_filename), bbox_inches='tight')
    print('Have written file to ' + fig_filename)

"""The main function

This reads the statistic data in csv file, then plot the charts
"""
if __name__ == "__main__":
    # ------------------------------------------------------------------------------------------
    # 1. read and collect results
    # ------------------------------------------------------------------------------------------
    if len(sys.argv) < 3:
        print("Error: should enter the comparison mode!")
        print("Usage: python generate_plots.py <input_folder> <compare_mode>")
        print("\t + compare_mode 0: \"delay\" (default)")
        print("\t + compare_mode 1: \"balancing\" overhead")
        exit(1)
    mode = sys.argv[2]
    input_folder = sys.argv[1]
    folder_tokens = input_folder.split('_')

    input_files = os.listdir(input_folder)
    dataset = []
    for i in range(len(input_files)):
        dataset.append([])

    for f in input_files:
        print("Reading: {}".format(f))
        name_tokens = f.split('_')
        O_balancecalculation = int(re.findall(r'\d+', name_tokens[2])[0])
        O_delay = int(re.findall(r'\d+', name_tokens[-1])[0])
        print('O_balancingcalculation={}, O_delay={}'.format(O_balancecalculation, O_delay))
        print('-------------------------------------')

        dframe = read_queue_status_results(os.path.join(input_folder, f))
        if mode == "delay":
            if O_delay == 1:
                idx = 0
            elif O_delay == 2:
                idx = 1
            elif O_delay == 5:
                idx = 2
            elif O_delay == 10:
                idx = 3
            elif O_delay == 20:
                idx = 4
        elif mode == "balancing":
            if O_balancecalculation == 1:
                idx = 0
            elif O_balancecalculation == 2:
                idx = 1
            elif O_balancecalculation == 5:
                idx = 2
            elif O_balancecalculation == 10:
                idx = 3
            elif O_balancecalculation == 20:
                idx = 4

        dataset[idx] = dframe

    # ------------------------------------------------------------------------------------------
    # 2. plot the chart
    # ------------------------------------------------------------------------------------------
    token = 0
    if mode == "delay":
        token = O_balancecalculation
    elif mode == "balancing":
        token = O_delay
    plot_queue_status(dataset, mode, token)