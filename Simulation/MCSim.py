import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from Simulation.users.utils import calculate_age
from Simulation.asset_classes.forms import getAssetClass
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
    output = np.zeros((n_yrs+1, sim_data.num_exp))

    # Run the simulation with the configuration based on the UI
    asset_class = getAssetClass(scenario.ac_index)
    run_simulation(scenario, sim_data, asset_class.avg_ret, asset_class.std_dev, n_yrs, output)

    return plot_output(output, sim_data.num_sim_bins)


def run_simulation(scenario, sim_data, invest_avg, invest_std_dev, n_yrs_sim, output):
    # Calculate the age at which each spouse will take social security
    s1ssa_sim = calculate_age(scenario.ss_date, scenario.birthdate)
    if scenario.has_spouse:
        s2ssa_sim = calculate_age(scenario.s_ss_date, scenario.s_birthdate)

    # Run the experiments
    for experiment in range(sim_data.num_exp):

        # These variables need to be re-initialized before every experiment
        s1_age = scenario.current_age
        if scenario.has_spouse:
            s2_age = scenario.s_current_age

        # Set the initial income for the primary user
        if s1_age < scenario.retirement_age:        # Working
            s1_income = scenario.current_income

        elif s1_age <= scenario.ret_job_ret_age:    # Partially retired
            s1_income = scenario.ret_income

        else:                                       # Fully retired
            s1_income = 0

        # Set the initial income for the spouse
        if scenario.has_spouse:
            if s2_age < scenario.s_retirement_age:      # Working
                s2_income = scenario.s_current_income

            elif s2_age <= scenario.s_ret_job_ret_age:  # Partially retired
                s2_income = scenario.s_ret_income

            else:                                       # Fully retired
                s2_income = 0

        # Set the initial social security amount to 0.
        s1ss = 0
        s2ss = 0

        nestegg = scenario.nestegg
        drawdown = scenario.drawdown

        # Generate a random sequence of investment annual returns based on a normal distribution
        s_invest = sim(invest_avg, invest_std_dev, n_yrs_sim)

        # Generate a random sequence of annual inflation rates using a normal distribution
        s_inflation = sim(sim_data.inflation[0], sim_data.inflation[1], n_yrs_sim)

        # Generate a random sequence of annual spend decay
        s_spend_decay = sim(sim_data.spend_decay[0], sim_data.spend_decay[1], n_yrs_sim)

        # Generate a random sequence of social security cost of living increases
        cola = sim(sim_data.cola[0], sim_data.cola[1], n_yrs_sim)

        # Record the nestegg starting point in the output list
        output[0][experiment] = nestegg

        for year in range(n_yrs_sim):
            s1_age += 1
            if scenario.has_spouse:
                s2_age += 1

            # Calculate the primary user's new salary, nestegg and drawdown amount
            if s1_age < scenario.retirement_age:            # Working
                nestegg += s1_income * scenario.savings_rate
                s1_income *= s_inflation[year]

            elif s1_age == scenario.retirement_age:         # Year of retirement
                s1_income = scenario.ret_income
                drawdown *= s_inflation[year]
                drawdown *= (1.0 - s_spend_decay[year])
                if (nestegg > 0):
                    nestegg -= drawdown
                nestegg += s1_income


            elif s1_age < scenario.ret_job_ret_age:         # Partially retired
                drawdown *= s_inflation[year]
                drawdown *= (1.0 - s_spend_decay[year])
                if (nestegg > 0 ):
                    nestegg -= drawdown
                nestegg += s1_income
                s1_income *= s_inflation[year]

            else:                                           # Fully retired
                s1_income = 0
                drawdown *= s_inflation[year]
                drawdown *= (1.0 - s_spend_decay[year])
                if (nestegg > 0 ):
                    nestegg -= drawdown

            # For spouse, just adjust the income
            if scenario.has_spouse:
                if s2_age < scenario.s_retirement_age:  # Working
                    nestegg += s1_income * scenario.savings_rate
                    s2_income *= s_inflation[year]

                elif s2_age == scenario.s_retirement_age:  # Year of retirement
                    s2_income = scenario.s_ret_income

                elif s2_age < scenario.s_ret_job_ret_age:  # Partially retired
                    s2_income *= s_inflation[year]

                else:  # Fully retired
                    s2_income = 0


            # Add windfall to the nestegg
            if s1_age == scenario.windfall_age:
                nestegg += scenario.windfall_amount

            # Add SS to the nestegg
            if s1_age == s1ssa_sim:
                s1ss = scenario.ss_amount
                nestegg += s1ss
            if s1_age > s1ssa_sim :
                s1ss *= cola[year]
                nestegg += s1ss

            if s2_age == s2ssa_sim:
                s2ss = scenario.s_ss_amount
                nestegg += s2ss
            if s2_age > s2ssa_sim:
                s2ss *= cola[year]
                nestegg += s2ss

            # Grow the nestegg
            nestegg *= (1+s_invest[year])

            if (s1_age > scenario.ret_job_ret_age) and (nestegg < 0):
                nestegg = 0.0
            output[year+1][experiment] = nestegg  # Record the final nestegg in the output list
    return


def plot_output(output, num_sim_bins):
    img = io.BytesIO()
    for i in range(output.shape[0]):
        output[i].sort()

    year = output.shape[0] - 1  # index of the year to graph
    num_exp = output.shape[1]

    n_graphs = 2  # The final year and the percentile graph

    # Don't display the top 5% because they are part of a "long tail" and mess up the visuals; Leave min at 0
    min_index = 0
    max_index = int(0.95 * num_exp) - 1
    plt.figure(figsize=(8, 6.5 * n_graphs))
    plt.subplots(n_graphs, 1, figsize=(8, 12))

    fig_num = 1
    plt.subplot(n_graphs, 1, fig_num)

    g_min = output[year][min_index]  # This is the min that we will graph
    g_max = output[year][max_index]  # This is the max that we will graph

    # This is to keep np.arange from crashing if g_max is too small
    if g_max < num_sim_bins:
        g_max = num_sim_bins
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

    ax.set_title('Year {year:.0f}'.format(year=year + 1))

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
    med = output[year][int(num_exp / 2)]
    plt.axvline(med + binsize / 2, color='g', linestyle='solid', linewidth=1)
    plt.text(med + xlen / 50, ypos - yinc, 'Median: ${0:,.0f}'.format(med), color='g')

    # Put a line for the average and label it
    avg = sum(output[year]) / num_exp
    plt.axvline(avg + binsize / 2, color='b', linestyle='solid', linewidth=1)  # Mean
    plt.text(avg + xlen / 50, ypos - 2 * yinc, 'Average: ${0:,.0f}'.format(avg), color='b')

    xpos = xmin + 0.5 * xlen

    plt.text(xpos, ypos - 10 * yinc,
             'Percentage over 0: {0:,.2f}%'.format(100 * (sum(i > 0.0 for i in output[year]) / num_exp)))

    fig_num += 1
    fiv_pct = output[:, int(0.95 * num_exp)]
    ten_pct = output[:, int(0.9 * num_exp)]
    t5_pct = output[:, int(0.75 * num_exp)]
    fif_pct = output[:, int(0.5 * num_exp)]
    s5_pct = output[:, int(0.25 * num_exp)]
    nt_pct = output[:, int(0.1 * num_exp)]
    n5_pct = output[:, int(0.05 * num_exp)]

    plt.subplot(n_graphs, 1, fig_num)
    g_max = max(fiv_pct)  # This is the max that we will graph
    plt.xlim(0, year)
    plt.ylim(0, g_max + 3000000)

    # Format the x axis so it shows normal number format with commas (not scientific notation)
    ax = plt.gca()
    ax.get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    ax.get_yaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda y, p: format(int(y / 1000000), ',')))

    line1 = ax.plot(fiv_pct, marker='o', markerfacecolor='red', markersize=2, linewidth=1, label="5%")
    line2, = ax.plot(ten_pct, marker='o', markerfacecolor='blue', markersize=2, linewidth=1, label="10%")
    line3, = ax.plot(t5_pct, marker='o', markerfacecolor='purple', markersize=2, linewidth=1, label="25%")
    line4, = ax.plot(fif_pct, marker='o', markerfacecolor='black', markersize=2, linewidth=1, label="50%")
    line5, = ax.plot(s5_pct, marker='o', markerfacecolor='orange', markersize=2, linewidth=1, label="75%")
    line6, = ax.plot(nt_pct, marker='o', markerfacecolor='green', markersize=2, linewidth=1, label="90%")
    line7, = ax.plot(n5_pct, marker='o', markerfacecolor='pink', markersize=2, linewidth=1, label="95%")
    ax.legend((line1, line2, line3, line4, line5, line6, line7), ('2%', '10%', '25%', '50%', '75%', '90%', '98%'))
    ax.legend(loc='upper left')

    vert_range = g_max + 3000000
    yinc = vert_range/20
    y_start = .944*vert_range

    # Plot the final outputs next to the legend entries
    plt.text((year / 6.9), y_start - 0*yinc, '${0:,.0f}'.format(fiv_pct[year]), color='red')
    plt.text((year / 6.9), y_start - 1*yinc, '${0:,.0f}'.format(ten_pct[year]), color='blue')
    plt.text((year / 6.9), y_start - 2*yinc, '${0:,.0f}'.format(t5_pct[year]), color='purple')
    plt.text((year / 6.9), y_start - 3*yinc, '${0:,.0f}'.format(fif_pct[year]), color='black')
    plt.text((year / 6.9), y_start - 4*yinc, '${0:,.0f}'.format(s5_pct[year]), color='orange')
    plt.text((year / 6.9), y_start - 5*yinc, '${0:,.0f}'.format(nt_pct[year]), color='green')
    plt.text((year / 6.9), y_start - 6*yinc, '${0:,.0f}'.format(n5_pct[year]), color='pink')

    plt.xlabel('Year')
    plt.ylabel('Portfolio value($M)')

    ax.set_title('Outcome percentiles by year')

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

# The following S&P 500 and inflation data are based on info I found on the net
# Initialize Inflation data#inflation_mean = 1.027
# inflation = [[1.027, 0.011]]

# Amex reports that a typical retiree spends 2% less every year they are in retirement. Model this as a probability
# distribution with a lot of variability (1 standard deviation is 10%)
# spend_decay = [[0.02, 0.001]]
