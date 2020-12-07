import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from Simulation.users.utils import calculate_age
import io
import base64
from itertools import chain


mpl.use('Agg')
plt.style.use('ggplot')


def do_sim(sim_data, scenario) -> plt.figure():

    # Number of years to simulate
    n_yrs = max(scenario.lifespan_age - scenario.current_age, scenario.s_lifespan_age - scenario.s_current_age)

    # output is an numpy.ndarray which holds the simulation results
    # [year][experiment]output
    output = np.zeros((n_yrs, sim_data.num_exp))

    # Provide this temporarily. Need to support "Asset classes" in the future
    investment = [[1.09391, 0.197028],
                  [(1.09391 + 1.03) / 2, 0.197028 / 2],
                  [1.04, 0.01]]
    # Run the simulation with the configuration based on the UI
    run_simulation(scenario, sim_data, investment[1], n_yrs, output)

    return plot_output(output, sim_data.num_sim_bins)


def run_simulation(scenario, sim_data, inv_sim, n_yrs_sim, output):

    # Calculate the age at which each spouse will take social security
    s1ssa_sim = calculate_age(scenario.start_ss_date, scenario.birthdate)
    s2ssa_sim = calculate_age(scenario.s_start_ss_date, scenario.s_birthdate)

    # Run the experiments
    for experiment in range(sim_data.num_exp):
        # These variables need to be re-initialized before every experiment
        s1_age = scenario.current_age
        s2_age = scenario.s_current_age

        if s1_age >= scenario.retirement_age:
            s1_income = scenario.ret_income
        else:
            s1_income = scenario.current_income

        if s2_age >= scenario.s_retirement_age:
            s2_income = scenario.s_ret_income
        else:
            s2_income = scenario.s_current_income

        # Starting assumption is SS is currently zero
        s1ss = 0
        s2ss = 0

        nestegg = scenario.nestegg
        drawdown = scenario.drawdown

        # Generate a random sequence of investment annual returns based on a normal distribution
        s_invest = sim(inv_sim[0], inv_sim[1], n_yrs_sim)

        # Generate a random sequence of annual inflation rates using a normal distribution
        s_inflation = sim(sim_data.inflation[0], sim_data.inflation[1], n_yrs_sim)

        # Generate a random sequence of annual spend decay
        s_spend_decay = sim(sim_data.spend_decay[0], sim_data.spend_decay[1], n_yrs_sim)

        for year in range(n_yrs_sim):
            s1_age += 1
            s2_age += 1

            # Spend the nestegg
            nestegg -= drawdown
            drawdown *= s_inflation[year]
            drawdown *= (1.0 - s_spend_decay[year])

            if s1_age == scenario.retirement_age:
                s1_income = scenario.ret_income

            # At retirement, switch income to be Linda's second job income
            if s2_age == scenario.s_retirement_age:
                s2_income = scenario.s_ret_income

            # Increase income based on inflation. When final ret age is reached, set income to zero
            if s1_age <= scenario.ret_job_ret_age:
                s1_income = s1_income * s_inflation[year]
            else:
                s1_income = 0

            # Same for Linda
            if s2_age <= scenario.s_ret_job_ret_age:
                s2_income = s2_income * s_inflation[year]
            else:
                s2_income = 0

            # Add windfall to the nestegg
            if s1_age == scenario.windfall_age:
                nestegg += scenario.windfall_amount

            # Add SS to the nestegg
            if s1_age >= s1ssa_sim:
                s1ss = scenario.ss_amount * (sim_data.cola ** year)

            if s2_age >= s2ssa_sim:
                s2ss = scenario.s_ss_amount * (sim_data.cola ** year)

            # Add the income to the nestegg
            nestegg += (s1_income + s2_income + s1ss + s2ss)

            # Grow the nestegg
            nestegg *= s_invest[year]
            output[year][experiment] = nestegg  # Record the final nestegg in the output list
    return


def plot_output(output, num_sim_bins):
    img = io.BytesIO()
    for i in range(output.shape[0]):
        output[i].sort()

    # This is the year we will plot - TEMPORARY
    years = output.shape[0]
    num_exp = output.shape[1]

    n_graphs = int(years/5) + 3

    # Don't display the top 2% because they are part of a "long tail" and mess up the visuals; Leave min at 0
    min_index = 0
    max_index = int(0.98 * num_exp) - 1
    plt.figure(figsize=(8, 6.5*n_graphs))
    plt.subplots(n_graphs, 1, figsize=(8, 50))

    # concatenated range will be 0, 10, 20 and then include the last year of simulation
    concatenated_range = chain(range(0, years, 5), range(years-1, years))
    fig_num=1
    for year in concatenated_range:
        plt.subplot(n_graphs, 1, fig_num)
        fig_num += 1
        g_min = output[year][min_index]  # This is the min that we will graph
        g_max = output[year][max_index]  # This is the max that we will graph

        binsize = (g_max - g_min) / num_sim_bins
        bins = np.arange(g_min, g_max, binsize)

        plt.xlim(g_min, g_max)

        # Format the x axis so it shows normal number format with commas (not scientific notation)
        ax = plt.gca()

        ax.get_xaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        ax.get_xaxis().set_major_locator(plt.MaxNLocator(5))

        plt.xlabel('Final portfolio value')
        plt.ylabel('Experiment count')

        n, arr, patches = plt.hist(output[year], bins=bins)


        ax.set_title('Year {year:.0f}'.format(year=year+1))

        ypos = n[np.argmax(n)] + 2  # Y position of the bin with the maximum count

        # These are the logical coordinates of the graph
        xmin = output[year][min_index]
        xmax = output[year][max_index]
        xlen = xmax - xmin

        yinc = ypos / 31  # Determined empirically, based on font and graph size

        # Put a line for the mode and label it
        mode = arr[np.argmax(n)]
        plt.axvline(mode + binsize / 2, color='k', linestyle='solid', linewidth=1)  # Mode
        plt.text(mode + xlen / 50, ypos, 'Mode: ${0:,.0f}'.format(mode), color='k')

        # Put a line for the median and label it
        med = output[year][int(num_exp/2)]
        plt.axvline(med + binsize / 2, color='g', linestyle='solid', linewidth=1)
        plt.text(med + xlen / 50, ypos - yinc, 'Median: ${0:,.0f}'.format(med), color='g')

        # Put a line for the average and label it
        avg = sum(output[year]) / num_exp
        plt.axvline(avg + binsize / 2, color='b', linestyle='solid', linewidth=1)  # Mean
        plt.text(avg + xlen / 50, ypos - 2 * yinc, 'Average: ${0:,.0f}'.format(avg), color='b')

        xpos = xmin + 0.5 * xlen

        plt.text(xpos, ypos - 10 * yinc,
                 'Percentage over 0: {0:,.2f}%'.format(100 * (sum(i >= 0 for i in output[year]) / num_exp)))

    two_pct = output[:, int(0.02*num_exp)]
    ten_pct = output[:, int(0.1*num_exp)]
    t5_pct = output[:, int(0.25 * num_exp)]
    fif_pct = output[:, int(0.5 * num_exp)]
    s5_pct = output[:, int(0.75 * num_exp)]
    nt_pct = output[:, int(0.9 * num_exp)]
    n8_pct = output[:, int(0.98 * num_exp)]

    plt.subplot(n_graphs, 1, fig_num)
    g_max = n8_pct[years-1]  # This is the max that we will graph

    plt.xlim(1, years)
    plt.ylim(0, g_max+3000000)

    # Format the x axis so it shows normal number format with commas (not scientific notation)
    ax = plt.gca()
    ax.get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.get_yaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda y, p: format(int(y/1000000), ',')))

    plt.plot(two_pct, marker='o', markerfacecolor='blue', markersize=3, color='blue', linewidth=2)
    plt.plot(ten_pct, marker='o', markerfacecolor='blue', markersize=3, color='blue', linewidth=2)
    plt.plot(t5_pct, marker='o', markerfacecolor='blue', markersize=3, color='blue', linewidth=2)
    plt.plot(fif_pct, marker='o', markerfacecolor='blue', markersize=3, color='blue', linewidth=2)
    plt.plot(s5_pct, marker='o', markerfacecolor='blue', markersize=3, color='blue', linewidth=2)
    plt.plot(nt_pct, marker='o', markerfacecolor='blue', markersize=3, color='blue', linewidth=2)
    plt.plot(n8_pct, marker='o', markerfacecolor='blue', markersize=3, color='blue', linewidth=2)

    plt.legend()

    plt.xlabel('Year')
    plt.ylabel('Portfolio value($M)')

    ax.set_title('Percentiles: 2/10/25/50/75/90/98')

    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    return plot_url


# Returns a random sequence of numbers of length num that are randomly drawn from the specified normal distribution
def sim(mean, stddev, num):
    return np.random.normal(mean, stddev, num)


# Some one time, large ticket items
# wedding_cost = -40000  # x4
# bathroom_cost = -15000  # x3
# kitchen_cost = -15000  # x1

# Social security data per year if we wait until 62/66.5/70
# s1_ss_at_62 = 25464  # at 62 years
# s1_ss_at_66 = 35460  # at 66 years and 6 months
# s1_ss_at_70 = 45612  # at 70

# s2_ss_at_62 = 18348  # at 62
# s2_ss_at_66 = 28872  # at 66 years and 6 months
# s2_ss_at_70 = 37476  # at 70

# investment = [[1.09391, 0.197028],
#              [(1.09391 + 1.03) / 2, 0.197028 / 2],
#              [1.04, 0.01]]

# The following S&P 500 and inflation data are based on info I found on the net
# Initialize Inflation data#inflation_mean = 1.027
# inflation = [[1.027, 0.011]]

# Amex reports that a typical retiree spends 2% less every year they are in retirement. Model this as a probability
# distribution with a lot of variability (1 standard deviation is 10%)
# spend_decay = [[0.02, 0.001]]
