import re
import os
import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# read file
# folders = './data/k_estimator'
input_folders = sys.argv[1]
if input_folders == None:
  print('Error: should enter the input!')
  print('Usage: python generate_plot.py <input_folders>')

files = os.listdir(input_folders)
dataframes = []
for i in range(len(files)):
  dataframes.append([])
for f in files:
  if 'example' in f:
    tokens = f.split('_')
    example = int(re.findall(r'\d+', tokens[0])[0])
    df = pd.read_csv(os.path.join(input_folders,f))
    dataframes[example-1] = df
  else:
    df = pd.read_csv(os.path.join(input_folders,f))
    dataframes[-1] = df

# create grid for multiple
gs = gridspec.GridSpec(2,3)
fig = plt.figure(figsize=(16,10))
ax1 = plt.subplot(gs[0,:])
ax2 = plt.subplot(gs[1,0])
ax3 = plt.subplot(gs[1,1])
ax4 = plt.subplot(gs[1,2])

# set style for the plots
# sns.set_style("darkgrid", {"axes.facecolor": ".9"})
sns.set_style("whitegrid", {"grid.color": ".6", "grid.linestyle": ":"})
# sns.set_axes_style("whitegrid")

# find y limit
kmax_example1 = np.max(dataframes[0]['K'])
kmax_example2 = np.max(dataframes[1]['K'])
kmax_example3 = np.max(dataframes[2]['K'])
ymax = np.max([kmax_example1, kmax_example2, kmax_example3])
ylimit = int(ymax+1000)

# plot latency and bandwidth graph on three systems
df_bw_latency= dataframes[-1]
size_values = list(df_bw_latency[df_bw_latency['system'] == 'coolmuc2']['size(bytes)'].values)
size_string = []
for s in size_values:
  s_int = s/1024
  if s_int > 1:
    s_int = int(s_int)
  size_string.append(str(s_int))
# re-generate the x-axis ticks
full_size_values = list(df_bw_latency['size(bytes)'].values)
x_range = []
for i in range(3):
  for j in range(len(size_values)):
    x_range.append(j)
# plot the 1st-twinx chart
plot_ax1 = sns.lineplot(data=df_bw_latency, ax=ax1, x=x_range, y="bw(MB/s)", hue="system", palette="dark", style="system", markers=["o","o","o"])
ax1.grid(visible=True, which='major', color='grey', linewidth=0.5)
ax1.set_xticks(range(len(size_values)), labels=size_string)
ax1.legend(loc='upper left')
# plot the 2nd-twinx chart
ax1_twinx = plot_ax1.axes.twinx()
plot_ax1_twinx = sns.lineplot(data=df_bw_latency, ax=ax1_twinx, x=x_range, y="latency(us)", hue="system", palette="dark", style="system", markers=["^","^","^"])
ax1_twinx.legend(loc='lower right')
ax1_twinx.set_ylabel('Latency (us)')
# ax1.set_ylim(0, ylimit)
ax1.set_yscale('log')
ax1.set_xlabel('message size (KB)')
ax1.set_ylabel('BW (MB/s)')
ax1.set_title('(A) Latency and Bandwidth with OSU Benchmark', fontweight ="bold")

# plot k estimated values in the 1st case, num. underloaded < num. overloaded
df_kestimate_example1 = dataframes[0]
k_size_values = list(df_kestimate_example1[df_kestimate_example1['system'] == 'coolmuc2']['task_size(MB)'].values)
k_size_string = []
for ks in k_size_values:
  sval = int(ks * 1024)
  k_size_string.append(str(sval))
# regenerate the x-axis ticks
full_k_size_values = list(df_kestimate_example1['task_size(MB)'].values)
k_x_range = []
for i in range(3):
  for j in range(len(k_size_values)):
    k_x_range.append(j)
# plot the charts
sns.lineplot(data=df_kestimate_example1, ax=ax2, x=k_x_range, y="K", hue="system", palette="dark", style="system", markers=["s","s","s"])
ax2.grid(visible=True, which='major', color='grey', linewidth=0.5)
ax2.set_xticks(range(len(k_size_values)), labels=k_size_string)
# ax2.set_ylim(-1, ylimit)
ax2.set_ylim( (pow(10,3),pow(10,7)) )
ax2.ticklabel_format(axis='y', style='scientific')
ax2.set_yscale('log')
ax2.set_xlabel('task size (KB)')
ax2.set_ylabel('K bound')
ax2.set_title(r'(B) Case: $R_{imb}$=1.5, P=8,' + '\n' + 'num.slowdown.procs=2' + '\n' + '$P_{overloaded} < P_{underloaded}$', fontweight ="bold", y=0.0)

# plot k estimated values in the 2nd case, num. underloaded = num. overloaded
df_kestimate_example2 = dataframes[1]
sns.lineplot(data=df_kestimate_example2, ax=ax3, x=k_x_range, y="K", hue="system", palette="dark", style="system", markers=["s","s","s"])
ax3.grid(visible=True, which='major', color='grey', linewidth=0.5)
ax3.set_xticks(range(len(k_size_values)), labels=k_size_string)
# ax3.set_ylim(-1, ylimit)
ax3.set_ylim( (pow(10,3),pow(10,7)) )
ax3.set_yscale('log')
ax3.set_xlabel('task size (KB)')
ax3.set(ylabel=None)
# ax3.set_ylabel('K bound')
ax3.set_title(r'(C) Case: $R_{imb}$=0.7, P=8,' + '\n' + 'num.slowdown.procs=4' + '\n' + '$P_{overloaded} = P_{underloaded}$', fontweight ="bold", y=0.0)

# plot k estimated values in the 3rd case, num. underloaded > num. overloaded
df_kestimate_example3 = dataframes[2]
sns.lineplot(data=df_kestimate_example3, ax=ax4, x=k_x_range, y="K", hue="system", palette="dark", style="system", markers=["s","s","s"])
ax4.grid(visible=True, which='major', color='grey', linewidth=0.5)
ax4.set_xticks(range(len(k_size_values)), labels=k_size_string)
# ax4.set_ylim(-1, ylimit)
ax4.set_ylim( (pow(10,3),pow(10,7)) )
ax4.set_yscale('log')
ax4.set_xlabel('task size (KB)')
ax4.set(ylabel=None)
# ax4.set_ylabel('K bound')
ax4.set_title(r'(D) Case: $R_{imb}$=0.3, P=8,' + '\n' + 'num.slowdown.procs=6' + '\n' + '$P_{overloaded} > P_{underloaded}$', fontweight ="bold", y=0.0)

# plt.show()

# save the figure
plt.savefig('./lat_bw_and_k_estimator_avg_bound.pdf', bbox_inches='tight')
