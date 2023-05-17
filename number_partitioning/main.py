import argument
import greedy 
import kk
import dp

import random
import numpy as np
import time
import sys

# ----------------------------------------------------
# Util Functions
# ----------------------------------------------------
def rand_soln_stan(size):
    S = []
    for i in range(size):
        s = 1 if (random.random() < 0.5) else -1
        S.append(s)
    return S

def rand_soln_pp(size):
    P = []
    for i in range(size):
        p = int(random.random() * size)
        P.append(p)
    return P

def gen_instance(size):
    r_max = 10**12
    return [random.randint(1, r_max) for i in range(size)]

# ----------------------------------------------------
# Algorithms
# ----------------------------------------------------


# ----------------------------------------------------
# Main Function
# ----------------------------------------------------
""" 
usage: partition [-h] [--numbers NUMBERS] [--grouplen GROUPLEN]
                 [--algorithm {greedy,kk,dp}] [--version]

optional arguments:
  -h, --help            show this help message and exit
  --numbers NUMBERS     integer numbers to be partitioned, seperated by comma
  --grouplen GROUPLEN   length of groups to hold the partitioned integer
                        numbers, default is 2
  --algorithm {greedy,kk,dp}
                        select partition algorithms, available options are
                        greedy, kk and dp
  --version             print version
"""

""" 
root@foo:~# partition --numbers 1,2,3,4,5 --grouplen 2 --algorithm greedy
    Partition 1,2,3,4,5 into 2 groups, using algorithm: greedy
    Group: 0, numbers: [5, 2, 1]
    Group: 1, numbers: [4, 3]
    Min group sum: 7, Max group sum: 8, difference: 1
    Group(s) with min sum: [4, 3]
    Group(s) with max sum: [5, 2, 1]
    ([[5, 2, 1], [4, 3]], 1)
"""

if __name__ == "__main__":

    # measure time for the whole program
    start_time = time.time()

    
    # parse the arguments into inputs
    parser = argument.get_parser()
    args = parser.parse_args()
    if args.version:
        print("partition v" + "0.1.2")
        exit(1)

    number_list = [int(i) for i in args.numbers.split(",")]

    if args.algorithm == "greedy":
        groups = greedy.greedy(number_list, args.grouplen)
    elif args.algorithm == "kk":
        groups = kk.kk(number_list, args.grouplen)
    elif args.algorithm == "dp":
        #TODO: fix the dp algorithm bug
        groups = dp.dp(number_list, args.grouplen)
    else:
        sys.exit("unsupported partition algorithm: %s" % args.algorithm)
        
    print("Partition %s into %s groups, using algorithm: %s" % (args.numbers, args.grouplen, args.algorithm))
    min_groupsum = min([sum(i) for i in groups])
    max_groupsum = max([sum(i) for i in groups])
    min_groupsum_indices, max_groupsum_indices = [], []
    for i in range(len(groups)):
        print("Group: %s, numbers: %s"%(i, groups[i]))
        if sum(groups[i]) == min_groupsum:
            min_groupsum_indices.append(i)
        if sum(groups[i]) == max_groupsum:
            max_groupsum_indices.append(i)
    print("Min group sum: %s, Max group sum: %s, difference: %s" % (min_groupsum, max_groupsum, max_groupsum-min_groupsum))
    print("Group(s) with min sum: %s" % ",".join([str(groups[i]) for i in min_groupsum_indices]))
    print("Group(s) with max sum: %s" % ",".join([str(groups[i]) for i in max_groupsum_indices]))
    

    # measure time for the whole program
    end_time = time.time()
    prog_elapsed_time = end_time - start_time
    print("------------------------------------------------------")
    print("Program elapsed time: {} (s)".format(prog_elapsed_time))
    print("------------------------------------------------------")


    