import math
import numpy as np
import sys

def dp(number_list, group_len=2):

    # check the number of partitions
    if group_len != 2:
        sys.exit("Unsupported group length: %s for DP algorithm!" % group_len)

    # check information about the number list
    n = len(number_list)
    k = sum(number_list)
    s = int(math.floor(k/2))
    print("Info: amount(numbers)={}, sum={}, C_perfect={}".format(n, k, s))

    # create a matrix s+1 rows, n+1 columns
    p = np.zeros((s+1, n+1))
    # the first row is assigned 1
    p[0] = 1
    print("matrix p:")
    print(p)

    # the main loop for dynamic programming
    for i in range(1, s+1): # from row 1 to s
        for j in range(1, n+1): # from column 1 to n
            print("i={}, j={}, number_list[j-1]={}".format(i, j, number_list[j-1]))
            if i - number_list[j-1] >= 0:
                p[i][j] = p[i][j-1] or p[i-number_list[j-1]][j-1]
            else:
                p[i][j] = p[i][j-1]

    return [p[s],p[n]]