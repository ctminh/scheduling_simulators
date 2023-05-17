
""" Greedy algorithm to partition numbers

Input: an array of integer numbers, the default number of partitions is 2
Output: subsets of numbers
"""
def greedy(number_list, group_len=2):
    # create an empty arrray of each partition
    groups = [[] for i in range(group_len)]

    # get through all sorted number in the list by the decreasing order
    for i in sorted(number_list, reverse=True):

        # sort the groups by the increasing order of sum
        groups.sort(key=lambda x: sum(x))

        # append a new number to the group that has the smallest sum
        groups[0].append(i)
        # print("Groups: {}".format(groups))
    
    return groups