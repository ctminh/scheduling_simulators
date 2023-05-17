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
def plot_queue_status(queue_dataset):
    # extract data
    ax1_data = queue_dataset

    num_procs = len(queue_dataset)

    # create figure and axis objects with subplots()
    # set the size, 15 is width, 4 is height
    gs = gridspec.GridSpec(1,5)
    fig = plt.figure(figsize=(15,4))
    ax1 = plt.subplot(gs[0,0])
    ax2 = plt.subplot(gs[0,1])
    ax3 = plt.subplot(gs[0,2])
    ax4 = plt.subplot(gs[0,3])
    ax5 = plt.subplot(gs[0,4])

    # share x, y
    # ax1.sharex(ax4)
    # ax2.sharex(ax5)
    # ax3.sharex(ax6)
    xlimit = 350000

    # ---------------------------------------------------------
    # Line styles
    # ---------------------------------------------------------
    lcolors = ['black', 'blue', 'darkgreen', 'red', 'darkorange', 'purple', 'teal', 'yellow']
    legend_size = 8
    legend_labels = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']

    # ---------------------------------------------------------
    # 1. Case 1
    # ---------------------------------------------------------
    ax1.set_title('A')
    ax1_indices = np.arange(len(ax1_data[0]))
    for i in range(num_procs): # loop through the methods
        ax1.plot(ax1_indices, ax1_data[i], label=legend_labels[i], color=lcolors[i])
    ax1.set_ylabel("Queue length")
    ax1.set_xlim(0, xlimit)
    ax1.legend(fontsize=legend_size)
    ax1.grid()

    # show the plot
    plt.show()

    # save the figure
    # fig_filename = "./queue_decrease_vs_balancingcalculationoverhead.pdf"
    # plt.savefig(os.path.join("./", fig_filename), bbox_inches='tight')

"""The main function

This reads the statistic data in csv file, then plot the charts
"""
if __name__ == "__main__":
    # ------------------------------------------------------------------------------------------
    # 1. read and collect results
    # ------------------------------------------------------------------------------------------
    input_files = sys.argv[1]
    print("Read: {}".format(input_files))
    dframe = read_queue_status_results(input_files)

    # ------------------------------------------------------------------------------------------
    # 2. plot the chart
    # ------------------------------------------------------------------------------------------
    plot_queue_status(dframe)