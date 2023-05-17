import random
import numpy as np
import time
import sys

# ------------------------------------------------------------
# MAIN FUNCTION
# ------------------------------------------------------------
if __name__ == "__main__":

    # table tracking migation of tasks
    NUM_RANKS = 4
    TRACKING_TABLE = [0, 4, 10, 15]
    VICTIM_ARR = []

    # init to mimic the proact-mig-tracking table
    total_tasks_to_migrate = 0
    for i in range(NUM_RANKS):
        if TRACKING_TABLE[i] != 0:
            total_tasks_to_migrate += TRACKING_TABLE[i]
            VICTIM_ARR.append(i)
    
    # init a proact-mig-tasks array
    proact_mig_tasks_arr = np.zeros(total_tasks_to_migrate)
    
    loop = 0
    current_rank = 0
    current_vict = -1
    last_vict = -1
    ntasks_to_mig = 0
    rr_victim_idx = 0
    while(total_tasks_to_migrate != 0):
        print("Loop {}: total_tasks_to_migrate={}".format(loop, total_tasks_to_migrate))

        # check victim-by-victim
        current_vict = VICTIM_ARR[rr_victim_idx]
        ntasks_to_mig = TRACKING_TABLE[current_vict]
        if ntasks_to_mig > 0:
            print("        R{} migrates 1 task to R{} in total of {}".format(current_rank, current_vict, ntasks_to_mig))

            # add to the proact-mig-tasks arr
            proact_mig_tasks_arr[loop] = current_vict

            # update tracking table
            TRACKING_TABLE[current_vict] = TRACKING_TABLE[current_vict] - 1
            if TRACKING_TABLE[current_vict] == 0:
                print("        [Remove victim R{}, rr_victim_idx={}]".format(current_vict, rr_victim_idx))
                VICTIM_ARR.remove(current_vict)
            total_tasks_to_migrate = total_tasks_to_migrate - 1
            last_vict = current_vict

        # increase loop
        loop = loop + 1
        if rr_victim_idx >= len(VICTIM_ARR)-1:
            rr_victim_idx = 0
        else:
            rr_victim_idx = rr_victim_idx + 1

        print("------------------------------------------------")

    print("The rank order of proact-migration:")
    print(proact_mig_tasks_arr)
