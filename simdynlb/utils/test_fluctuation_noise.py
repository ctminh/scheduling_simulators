import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
import sys
import seaborn as sns
import matplotlib.gridspec as gridspec

# -----------------------------------------------------
# Main function
# -----------------------------------------------------
if __name__ == "__main__":

    # get the balancing and delay cost
    if len(sys.argv) < 5:
        print('Usage: python test_fluctuation_noise <balancing_cost> <delay_cost> <noise> <num_iters>')
        exit(1)

    balancing_cost = int(sys.argv[1])
    migration_delay_cost = int(sys.argv[2])
    noise = int(sys.argv[3])
    num_iters = int(sys.argv[4])

    # check noise value
    if noise > balancing_cost or noise > migration_delay_cost:
        print('Error: noise cannot be larger than the cost')
        exit(1)

    # determine min and max value
    min_balancing_cost = balancing_cost - noise
    max_balancing_cost = balancing_cost + noise
    min_delay = migration_delay_cost - noise
    max_delay = migration_delay_cost + noise

    # generate randomized overhead with noise over different iterations
    arr_iteration_idx = []
    arr_balancing_cost = []
    arr_migration_cost = []
    for i in range(num_iters):

        # seeding per iteration
        random.seed(i)
        arr_iteration_idx.append(i)

        # generate cost
        balancing_cost_val = random.randint(min_balancing_cost, max_balancing_cost)
        migration_cost_val = random.randint(min_delay, max_delay)
        arr_balancing_cost.append(balancing_cost_val)
        arr_migration_cost.append(migration_cost_val)

    # plot the charts for checking
    df_overhead = pd.DataFrame({
        'iter': arr_iteration_idx,
        'balancing_cost': arr_balancing_cost,
        'migration_cost': arr_migration_cost
    })

    df_overhead.plot(x='iter')
    plt.legend(fontsize=10)
    plt.grid()
    plt.show()



