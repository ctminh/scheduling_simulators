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

# create grid for multiple
gs = gridspec.GridSpec(1,3)
fig = plt.figure(figsize=(16,5))
ax1 = plt.subplot(gs[0,0])
ax2 = plt.subplot(gs[0,1])
ax3 = plt.subplot(gs[0,2])

# set style for the plots
sns.set_style("whitegrid", {"grid.color": ".6", "grid.linestyle": ":"})

# find y limit
kmax_example1 = np.max(dataframes[0]['K'])
kmax_example2 = np.max(dataframes[1]['K'])
kmax_example3 = np.max(dataframes[2]['K'])
ymax = np.max([kmax_example1, kmax_example2, kmax_example3])
ylimit = int(ymax+500000)

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
plt1 = sns.lineplot(data=df_kestimate_example1, ax=ax1, x=k_x_range, y="K", hue="system", palette="dark", style="system", markers=["s","s","s"])
ax1.grid(visible=True, which='major', color='grey', linewidth=0.5)
ax1.set_xticks(range(len(k_size_values)), labels=k_size_string)
# ax1.set_ylim(-1, ylimit)
ax1.set_ylim( (pow(10,3),pow(10,7)) )
ax1.ticklabel_format(axis='y', style='scientific')
ax1.set_yscale('log')
ax1.set_xlabel('task size (KB)')
ax1.set_ylabel('K bound')
ax1.set_title(r'(B) Case: $R_{imb}$=1.5, P=8,' + '\n' + 'num.slowdown.procs=2' + '\n' + '$P_{overloaded} > P_{underloaded}$', fontweight ="bold", y=0.0)

# plot k estimated values in the 2nd case, num. underloaded = num. overloaded
df_kestimate_example2 = dataframes[1]
plt2 = sns.lineplot(data=df_kestimate_example2, ax=ax2, x=k_x_range, y="K", hue="system", palette="dark", style="system", markers=["s","s","s"])
ax2.grid(visible=True, which='major', color='grey', linewidth=0.5)
ax2.set_xticks(range(len(k_size_values)), labels=k_size_string)
# ax2.set_ylim(-1, ylimit)
ax2.set_ylim( (pow(10,3),pow(10,7)) )
ax2.set_yscale('log')
ax2.set_xlabel('task size (KB)')
ax2.set(ylabel=None)
# ax2.set_ylabel('K bound')
ax2.set_title(r'(C) Case: $R_{imb}$=0.7, P=8,' + '\n' + 'num.slowdown.procs=4' + '\n' + '$P_{overloaded} = P_{underloaded}$', fontweight ="bold", y=0.0)

# plot k estimated values in the 3rd case, num. underloaded > num. overloaded
df_kestimate_example3 = dataframes[2]
plt3 = sns.lineplot(data=df_kestimate_example3, ax=ax3, x=k_x_range, y="K", hue="system", palette="dark", style="system", markers=["s","s","s"])
ax3.grid(visible=True, which='major', color='grey', linewidth=0.5)
ax3.set_xticks(range(len(k_size_values)), labels=k_size_string)
# ax3.set_ylim(-1, ylimit)
ax3.set_ylim( (pow(10,3),pow(10,7)) )
ax3.set_yscale('log')
ax3.set_xlabel('task size (KB)')
ax3.set(ylabel=None)
# ax3.set_ylabel('K bound')
ax3.set_title(r'(D) Case: $R_{imb}$=0.3, P=8,' + '\n' + 'num.slowdown.procs=6' + '\n' + '$P_{overloaded} < P_{underloaded}$', fontweight ="bold", y=0.0)

# plt.show()

# save the figure
plt.savefig('./lat_bw_and_k_estimator_minmax_bound.pdf', bbox_inches='tight')
