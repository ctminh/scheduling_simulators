import heapq
import sys
try:
    from Queue import LifoQueue
except ImportError:
    from queue import LifoQueue

""" Karmarkar-Karp heuristic algorithm to partition numbers

Input: an array of integer numbers, the default number of partitions is 2
Output: subsets of numbers
For example: S = {1, 2, 3, 4, 5}
    + create a heap, like a sorted array by descending order
        [(-5, 5), (-4, 4), ..., (-1, 1)]
    + pop the first 2 max numbers, 5, 4
    + then get the subtract (-1)
    + record the popped pair: (5, 4)
    + re-push the substract and the max num into the heap: (-1, 5) | heap: [(-3,3), (-2,2), (-1,1), (-1,5)]
    + redo until the len(heap) <= 1:
        (-3, 3), (-2, 2) | pair(3, 2), subtract(-1), re-push(-1, 3) | heap: [(-1,1), (-1,5), (-1,3)]
        (-1, 1), (-1, 5) | pair(1,5)
"""
def kk(number_list, group_len=2): # Karmarkar-Karp heuristic

    # check num of partitions, just support 2 groups
    if group_len != 2:
        sys.exit("Unsupported group length: %s for KK algorithm!" % group_len)
    
    # create the LIFO queue
    pairs = LifoQueue()
    group1, group2 = [], []

    # create an array of [(-n1,n1), (-n2,n2), ...] in number_list
    heap = [(-1*i, i) for i in number_list]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        # pop the first 2 max numbers
        i, labeli = heapq.heappop(heap)
        j, labelj = heapq.heappop(heap)
        print("[(i, labeli), (j, labelj)] = [({},{}), ({},{})]".format(i, labeli, j, labelj))

        # record the pair
        pairs.put((labeli, labelj))

        # re-add the subtract and the max number to the heap
        heapq.heappush(heap, (i-j, labeli))
        print("heappush: (i-j, labeli) = ({}, {})".format(i-j, labeli))
    
    print("--------------------------------------------------")
    
    # append group 1
    group1.append(heapq.heappop(heap)[1])
    # print("append Group1: {}".format(group1))
    
    while not pairs.empty():
        pair = pairs.get()
        print("get pair: {}".format(pair))
        if pair[0] in group1:
            group2.append(pair[1])
        elif pair[0] in group2:
            group1.append(pair[1])

    return [group1, group2]