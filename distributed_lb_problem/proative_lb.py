import random
import numpy as np
import time
import sys

# ------------------------------------------------------------
# SIM_GREADY_CUT ALGORITHM
# ------------------------------------------------------------
def simgreed_cut_lb(task_table, local_load_arr, num_local_tasks, remot_load_arr, num_remot_tasks):
    print("======================================================")
    NUM_RANKS = len(local_load_arr)
    max_load = np.max(local_load_arr)
    avg_load = np.average(local_load_arr)
    imb_ratio = (max_load - avg_load) / avg_load
    pre_imb_ratio = 0
    cut_counter = 0
    while imb_ratio > 0.15 and imb_ratio != pre_imb_ratio:
        print("CUT COUNTER = {}".format(cut_counter))
        print("------------------------------------------------------")
        total_load_info = np.array(local_load_arr) + np.array(remot_load_arr)

        # sort the load arr
        idx_srt_arr = np.argsort(total_load_info)
        print("Rank's positions by sorting the total load:")
        print(idx_srt_arr)

        # check rank by rank
        for r in range(NUM_RANKS):

            # get the position of the current rank (Rank r)
            pos_r = (np.where(idx_srt_arr == r)[0])[0]

            if pos_r >= NUM_RANKS/2:

                # check load info between src and vic
                load_r = total_load_info[r]
                n_local_tasks = num_local_tasks[r]
                pos_victim = NUM_RANKS - pos_r - 1
                rank_victim = idx_srt_arr[pos_victim]
                load_victim = total_load_info[rank_victim]
                print("\tR{}: victim=R{}, victim_load={}".format(r, rank_victim, load_victim))

                # calculate diff_load and num_tasks to migrate
                diff_load = load_r - load_victim
                local_load_r = local_load_arr[r]

                ntasks_to_migrate = 0
                if n_local_tasks != 0:
                    ntasks_to_migrate = int((diff_load/2) / (local_load_r/n_local_tasks))

                if ntasks_to_migrate >= n_local_tasks:
                    ntasks_to_migrate = n_local_tasks

                migrated_load = 0
                if ntasks_to_migrate != 0:
                    migrated_load = ntasks_to_migrate * (local_load_r/n_local_tasks)

                new_load_r = load_r - migrated_load
                new_load_v = load_victim + migrated_load
                print("\tR{}: migrates {} tasks to R{}".format(r, ntasks_to_migrate, rank_victim))
                print("\tNew load: R{}={:.3f}, V(R{})={:.3f}".format(r, new_load_r, rank_victim, new_load_v))

                # update new load
                local_load_arr[r] = local_load_arr[r] - migrated_load
                remot_load_arr[rank_victim] = remot_load_arr[rank_victim] + migrated_load

                # update new num of tassk in the queue
                num_local_tasks[r] = num_local_tasks[r] - ntasks_to_migrate
                num_remot_tasks[rank_victim] = num_remot_tasks[rank_victim] + ntasks_to_migrate

                # update TRACKING_TABLE
                # Rank r sends tasks to Rank victim
                task_table[r][r] = task_table[r][r] - ntasks_to_migrate
                task_table[r][rank_victim] = task_table[r][rank_victim] + ntasks_to_migrate

                # check new load & task queues
                print("\tupdated_load(R0, R1, R2, R3): {}".format(np.array(local_load_arr) + np.array(remot_load_arr)))
                print("\tlocal_queue: {}".format(num_local_tasks))
                print("\tremot_queue: {}".format(num_remot_tasks))
                print("\t----------------------------------------------")

        # record the current imb. ratio before updating it
        pre_imb_ratio = imb_ratio

        # update imbalance ratio
        new_max_load = np.max(np.array(local_load_arr) + np.array(remot_load_arr))
        new_avg_load = np.average(np.array(local_load_arr) + np.array(remot_load_arr))
        imb_ratio = (new_max_load - new_avg_load) / new_avg_load

        print("------------------------------------------------------")
        print("\tNew Imb.ratio: {:.5f}".format(imb_ratio))

        # increase cut_counter
        cut_counter += 1
        print("------------------------------------------------------")

# ------------------------------------------------------------
# DIST_GREADY_KNAP ALGORITHM
# ------------------------------------------------------------
def distgreed_knap_lb(task_table, local_load_arr, num_local_tasks, remot_load_arr, num_remot_tasks):
    print("======================================================")
    NUM_RANKS = len(local_load_arr)
    max_load = np.max(local_load_arr)
    avg_load = np.average(local_load_arr)
    imb_ratio = (max_load - avg_load) / avg_load

    total_load_info = np.array(local_load_arr) + np.array(remot_load_arr)

    # calculate load per task of each rank
    load_per_task = np.zeros((NUM_RANKS,), dtype=float)
    for i in range(NUM_RANKS):
        ntasks = task_table[i][i]
        load_per_task[i] = total_load_info[i]/ntasks

    # sort the load arr
    idx_srt_arr = np.argsort(total_load_info)
    print("Rank's positions by sorting the total load:")
    print(idx_srt_arr)

    # main loop of the algorithm
    for i in range(NUM_RANKS):

        # from the most underloaded rank
        victim = idx_srt_arr[i]
        victim_load = total_load_info[victim]
        if victim_load < avg_load:
            under_load = avg_load - victim_load

            print("------------------------------------------------------")
            print("VICTIM R{} is being processed...".format(victim))

            # from the most overloaded rank
            for j in range(NUM_RANKS-1, 0, -1):

                offloader = idx_srt_arr[j]
                offloader_load = total_load_info[offloader]
                over_load = offloader_load - avg_load

                if offloader_load > avg_load and over_load >= load_per_task[offloader]:
                    print("------------------------------------------------------")

                    # check over_load and under_load
                    numtasks_can_migrate = 0
                    migrated_load = 0.0
                    if over_load >= under_load:
                        numtasks_can_migrate =  int(under_load / load_per_task[offloader])
                        migrated_load = numtasks_can_migrate * load_per_task[offloader]
                    else:
                        numtasks_can_migrate = int(over_load / load_per_task[offloader])
                        migrated_load = numtasks_can_migrate * load_per_task[offloader]
                    print("   R{} (overload={:.3f}) migrates {} tasks to R{} (underload={:.3f}) | migrated_load={:.3f}".format(offloader, over_load, numtasks_can_migrate, victim, under_load, migrated_load))

                    # update under_load, and load of the offloader
                    under_load = under_load - migrated_load
                    local_load_arr[offloader] -= migrated_load
                    remot_load_arr[victim] += migrated_load
                    total_load_info[offloader] = local_load_arr[offloader] + remot_load_arr[offloader]
                    total_load_info[victim] = local_load_arr[victim] + remot_load_arr[victim]
                    print("   Updated Load: R{}[L{:.2f}, R{:.2f}], R{}[L{:.2f}, R{:.2f}]".format(offloader, local_load_arr[offloader], remot_load_arr[offloader], victim, local_load_arr[victim], remot_load_arr[victim]))

                    # update num_tasks local and remote
                    num_local_tasks[offloader] -= numtasks_can_migrate
                    num_remot_tasks[victim] += numtasks_can_migrate
                    task_table[offloader][offloader] -= numtasks_can_migrate
                    task_table[offloader][victim] += numtasks_can_migrate
                    print("   Updated Numtasks: R{}[L{}, R{}], R{}[L{}, R{}]".format(offloader, num_local_tasks[offloader], num_remot_tasks[offloader], victim, num_local_tasks[victim], num_remot_tasks[victim]))

                    # calculate the abs between new under_load and avg_load
                    abs_value = abs((local_load_arr[victim]+remot_load_arr[victim]) - avg_load)
                    print("   Abs value: new under_load and avg_load {}".format(abs_value))

                    if abs_value < load_per_task[offloader]:
                        break


def generate_uniform_tasks(task_queues, Rimb, max_task, numtasks, numranks):

    R0_load = max_task * numtasks
    max = R0_load
    avg = max / (Rimb + 1)
    print("GENERATE_UNIF_TASKS: Rimb={}, max={}, avg={}".format(Rimb, max, avg))

    sum_Ri_load = avg * numranks - max
    print("GENERATE_UNIF_TASKS: Sum(Ri_load)={}".format(sum_Ri_load))

    # create an array of load per rank
    load_arr = np.zeros((numranks,), dtype=float)

    for i in range(numranks):
        if i == 0:
            load_arr[i] = max
            print("\tR{}: load={}".format(i, load_arr[i]))
            load_per_task = max_task
            for t in range(numtasks):
                task_queues[i].append(load_per_task)
        elif i == numranks-1:
            load_arr[i] = sum_Ri_load - np.sum(load_arr[1:numranks-1])
            print("\tR{}: load={}".format(i, load_arr[i]))
            load_per_task = load_arr[i] / numtasks
            for t in range(numtasks):
                task_queues[i].append(load_per_task)
        elif i == 1:
            bnd_min = 0.1 * sum_Ri_load
            bnd_max = 0.5 * sum_Ri_load
            rnd_load = random.uniform(bnd_min, bnd_max)
            load_arr[i] = rnd_load
            print("\tR{}: load={}".format(i, load_arr[i]))
            load_per_task = load_arr[i] / numtasks
            for t in range(numtasks):
                task_queues[i].append(load_per_task)
        else:
            new_sum_Ri = sum_Ri_load - np.sum(load_arr[1:i])
            bnd_min = 0.2 * new_sum_Ri
            bnd_max = 0.7 * new_sum_Ri
            rnd_load = random.uniform(bnd_min, bnd_max)
            load_arr[i] = rnd_load
            print("\tR{}: load={}".format(i, load_arr[i]))
            load_per_task = load_arr[i] / numtasks
            for t in range(numtasks):
                task_queues[i].append(load_per_task)

    # check sum_Ri again
    # print("CHECK: Sum(Ri_load)={}".format(np.sum(load_arr[1:])))


# ------------------------------------------------------------
# MAIN FUNCTION
# ------------------------------------------------------------
if __name__ == "__main__":

    # measure time for the whole program
    start_time = time.time()

    # table tracking migation of tasks
    NUM_RANKS = 8
    # NUM_TASKS_PER_RANK = 13*16
    TRACKING_TABLE = []
    TASK_QUEUE_PER_RANK = []

    for r in range(NUM_RANKS):
        TASK_QUEUE_PER_RANK.append([])

    # generate tasks by imbalance ratio
    # print("------------------------------------------------------")
    # Rimb = 2.5
    # Mload = 0.5
    # generate_uniform_tasks(TASK_QUEUE_PER_RANK, Rimb, Mload, NUM_TASKS_PER_RANK, NUM_RANKS)
    # print("------------------------------------------------------")

    # init data to mimic the real apps
    local_load_info_arr = []
    remot_load_info_arr = []
    num_local_tasks_arr = []
    num_remot_tasks_arr = []
    for r in range(NUM_RANKS):

        local_load_info_arr.append(0)
        remot_load_info_arr.append(0)

        # num_local_tasks_arr.append(NUM_TASKS_PER_RANK)
        num_remot_tasks_arr.append(0)

        TRACKING_TABLE.append([])

        # for i in range(NUM_TASKS_PER_RANK):
        #     if r == 0:
        #         TASK_QUEUE_PER_RANK[r].append(0.022082/208)
        #     elif r == 1:
        #         TASK_QUEUE_PER_RANK[r].append(3.256885/208)
        #     elif r == 2:
        #         TASK_QUEUE_PER_RANK[r].append(7.909215/208)
        #     elif r == 3:
        #         TASK_QUEUE_PER_RANK[r].append(0.030997/208)
        #     elif r == 4:
        #         TASK_QUEUE_PER_RANK[r].append(0.042488/208)
        #     elif r == 5:
        #         TASK_QUEUE_PER_RANK[r].append(14.468595/208)
        #     elif r == 6:
        #         TASK_QUEUE_PER_RANK[r].append(14.213778/208)
        #     elif r == 7:
        #         TASK_QUEUE_PER_RANK[r].append(0.029059/208)
        #     elif r == 8:
        #         TASK_QUEUE_PER_RANK[r].append(0.022913/208)
        #     elif r == 9:
        #         TASK_QUEUE_PER_RANK[r].append(7.960334/208)
        #     elif r == 10:
        #         TASK_QUEUE_PER_RANK[r].append(3.262056/208)
        #     elif r == 11:
        #         TASK_QUEUE_PER_RANK[r].append(0.034173/208)
        #     elif r == 12:
        #         TASK_QUEUE_PER_RANK[r].append(0.028231/208)
        #     elif r == 13:
        #         TASK_QUEUE_PER_RANK[r].append(1.772048/208)
        #     elif r == 14:
        #         TASK_QUEUE_PER_RANK[r].append(1.752632/208)
        #     else:
        #         TASK_QUEUE_PER_RANK[r].append(0.019532/208)

        if r == 0:
            num_local_tasks_arr.append(800)
            for i in range(800):
                TASK_QUEUE_PER_RANK[r].append(18.454454/800)
        elif r == 1:
            num_local_tasks_arr.append(100)
            for i in range(100):
                TASK_QUEUE_PER_RANK[r].append(2.371473/100)
        elif r == 2:
            num_local_tasks_arr.append(50)
            for i in range(50):
                TASK_QUEUE_PER_RANK[r].append(1.630086/50)
        elif r == 3:
            num_local_tasks_arr.append(50)
            for i in range(50):
                TASK_QUEUE_PER_RANK[r].append(1.595835/50)
        elif r == 4:
            num_local_tasks_arr.append(50)
            for i in range(50):
                TASK_QUEUE_PER_RANK[r].append(1.240259/50)
        elif r == 5:
            num_local_tasks_arr.append(50)
            for i in range(50):
                TASK_QUEUE_PER_RANK[r].append(1.224187/50)
        elif r == 6:
            num_local_tasks_arr.append(90)
            for i in range(90):
                TASK_QUEUE_PER_RANK[r].append(2.150636/90)
        elif r == 7:
            num_local_tasks_arr.append(90)
            for i in range(90):
                TASK_QUEUE_PER_RANK[r].append(2.141610/90)

        for j in range(NUM_RANKS):
            if j == r:
                # TRACKING_TABLE[r].append(NUM_TASKS_PER_RANK)
                if j == 0:
                    TRACKING_TABLE[r].append(800)
                elif j == 1:
                    TRACKING_TABLE[r].append(100)
                elif j == 2:
                    TRACKING_TABLE[r].append(50)
                elif j == 3:
                    TRACKING_TABLE[r].append(50)
                elif j == 4:
                    TRACKING_TABLE[r].append(50)
                elif j == 5:
                    TRACKING_TABLE[r].append(50)
                elif j == 6:
                    TRACKING_TABLE[r].append(90)
                elif j == 7:
                    TRACKING_TABLE[r].append(90)
            else:
                TRACKING_TABLE[r].append(0)

    TRACKING_TABLE = np.array(TRACKING_TABLE)

    print("Rank \t Load")
    for r in range(NUM_RANKS):
        print("R{} \t {:7.3f}".format(r, np.sum(TASK_QUEUE_PER_RANK[r])))
        local_load_info_arr[r] = np.sum(TASK_QUEUE_PER_RANK[r])

    print("------------------------------------------------------")
    print("TRACKING_TABLE:")
    print(TRACKING_TABLE)


    # check the current imb_ratio
    max_load = np.max(local_load_info_arr)
    avg_load = np.average(local_load_info_arr)
    imb_ratio = (max_load - avg_load) / avg_load
    pre_imb_ratio = 0
    print("R_imb: {:.5f} | Threshold avg_load={:.3f}".format(imb_ratio, avg_load))

    # ------------------------------------------------------------
    # SIM_GREADY_CUT ALGORITHM
    # ------------------------------------------------------------
    # simgreed_cut_lb(TRACKING_TABLE, local_load_info_arr, num_local_tasks_arr, remot_load_info_arr, num_remot_tasks_arr)

    # ------------------------------------------------------------
    # DIST_GREADY_KNAP ALGORITHM
    # ------------------------------------------------------------
    distgreed_knap_lb(TRACKING_TABLE, local_load_info_arr, num_local_tasks_arr, remot_load_info_arr, num_remot_tasks_arr)

    print("======================================================")
    print("Local Task Queue: {} | Sum={}".format(num_local_tasks_arr, np.sum(num_local_tasks_arr)))
    print("Remot Task Queue: {} | Sum={}".format(num_remot_tasks_arr, np.sum(num_remot_tasks_arr)))
    print("Final TRACKING_TABLE:")
    print(TRACKING_TABLE)
    print("======================================================")
    print("------------------------------------------------------")
    print("Detail \t local_tasks \t remot_tasks \t numtasks_to_migrate")
    for r in range(NUM_RANKS):
        numtasks_to_migrate = ""
        for v in range(NUM_RANKS):
            if r != v and TRACKING_TABLE[r][v] != 0:
                numtasks = TRACKING_TABLE[r][v]
                numtasks_to_migrate += str(numtasks) + "(R" + str(v) + ") "
                # print("\tmigrates {} tasks to R{}".format(TRACKING_TABLE[r][v], v))

        print("R{} \t {} \t\t {} \t\t {}".format(r, TRACKING_TABLE[r][r], np.sum(TRACKING_TABLE[:,r])-TRACKING_TABLE[r][r], numtasks_to_migrate))

    print("------------------------------------------------------")
    print("Final Load:")
    print("{} | Sum={}".format(np.array(local_load_info_arr) + np.array(remot_load_info_arr), np.sum(np.array(local_load_info_arr) + np.array(remot_load_info_arr))))
    print("Local Load Arr:")
    print(np.array(local_load_info_arr))
    print("Remote Load Arr:")
    print(np.array(remot_load_info_arr))

    final_total_load_arr = np.array(local_load_info_arr) + np.array(remot_load_info_arr)
    final_max = np.max(final_total_load_arr)
    final_avg = np.average(final_total_load_arr)
    final_imb = (final_max - final_avg) / final_avg
    print("Final Imb.Ratio: {}".format(final_imb))

    # measure time for the whole program
    end_time = time.time()
    prog_elapsed_time = end_time - start_time
    print("------------------------------------------------------")
    print("Program elapsed time: {} (s)".format(prog_elapsed_time))
    print("------------------------------------------------------")
