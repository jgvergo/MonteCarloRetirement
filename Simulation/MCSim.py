from datetime import date
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io

def run_simulation(s1ra_sim, s2ra_sim, s1rra_sim, s2rra_sim, s1ssa_sim, s2ssa_sim,
                   inf_sim, inv_sim, spend_decay_sim, n_yrs_sim, num_exp, output, sim_num, df, ls_sim, progress_w=0):
    # Run the experiments
    for experiment in range(num_exp):

        # These variables need to be re-initialized before every experiment
        s1_age = s1_current_age
        s2_age = s2_current_age
        s1_income = s1_current_income
        s2_income = s2_current_income
        s1ss = 0
        s2ss = 0
        nestegg = nestegg_current
        drawdown = income_replacement * (s1_current_income + s2_current_income)

        # Generate a random sequence of investment annual returns based on a normal distribution
        s_invest = sim(inv_sim[0], inv_sim[1], n_yrs_sim)

        # Generate a random sequence of annual inflation rates using a normal distribution
        s_inflation = sim(inf_sim[0], inf_sim[1], n_yrs_sim)

        # Generate a random sequence of annual spend decay
        s_spend_decay = sim(spend_decay_sim[0], spend_decay_sim[1], n_yrs_sim)

        for i in range(n_yrs_sim):
            s1_age += 1
            s2_age += 1

            # Spend the nestegg
            nestegg -= drawdown
            drawdown *= s_inflation[i]
            drawdown *= (1.0 - s_spend_decay[i])

            # At retirement, switch income to be my second job income
            if s1_age == s1ra_sim:
                s1_income = s1_sec_job

            # At retirement, switch income to be Linda's second job income
            if s2_age == s2ra_sim:
                s2_income = s2_sec_job

            # Increase income based on inflation. When final ret age is reached, set income to zero
            if s1_age <= s1rra_sim:
                s1_income = s1_income * s_inflation[i]
            else:
                s1_income = 0

            # Same for Linda
            if s2_age <= s2rra_sim:
                s2_income = s2_income * s_inflation[i]
            else:
                s2_income = 0

            if s1_age == windfall_age:
                nestegg += windfall
            # Add SS to the nestegg
            if s1_age >= s1ssa_sim:
                if s1ssa_sim == 62:
                    s1ss = s1_ss_at_62 * (cola ** i)
                elif s1ssa_sim == 66:
                    s1ss = s1_ss_at_66 * (cola ** i)
                elif s1ssa_sim == 70:
                    s1ss = s1_ss_at_70 * (cola ** i)
                else:
                    print("Error in SS")

            if s2_age >= s2ssa_sim:
                if s2ssa_sim == 62:
                    s2ss = s2_ss_at_62 * (cola ** i)
                elif s2ssa_sim == 66:
                    s2ss = s2_ss_at_66 * (cola ** i)
                elif s2ssa_sim == 70:
                    s2ss = s2_ss_at_70 * (cola ** i)
                else:
                    print("Error in SS")

            # Add the income to the nestegg
            nestegg += (s1_income + s2_income + s1ss + s2ss)

            # Grow the nestegg
            nestegg *= s_invest[i]
        #        print('Final Drawdown = ', drawdown)
        output[experiment] = nestegg  # Record the final nestegg in the output list

    # Sort the output
    output.sort()

    # Calculate the key statistics
    o_max = max(output)
    o_min = min(output)
    avg = sum(output) / len(output)
    median = output[int(len(output) / 2)]

    # p0 is the percent of the experiments that resulted in a final value > 0
    p0 = 100 * (sum(i > 0 for i in output) / len(output))

    # Save the results in a dataframe
    df.iloc[sim_num] = [s1ra_sim, s2ra_sim, s1rra_sim, s2rra_sim, s1ssa_sim, s2ssa_sim, ls_sim,
                        inf_sim[0], inf_sim[1], inv_sim[0], inv_sim[1], spend_decay_sim[0], spend_decay_sim[1],
                        p0, median, avg, o_min, o_max, output]
    if progress_w != 0:
        progress_w.value = sim_num
    return sim_num


def plot_output(output,
                s1_ret_age, s2_ret_age,
                s1_ret_ret_age, s2_ret_ret_age,
                s1_ss_age, s2_ss_age,
                s1_lifespan,
                inflation_mean, inflation_stddev,
                invest_mean, invest_stddev,
                spend_decay_mean, spend_decay_stddev,
                windfall_amount):
    output.sort()
#    o_max = max(output)
#    o_min = min(output)
#    avg = sum(output) / len(output)

    # We don't display the bottom or top 2% because they are part of a "long tail" and mess up the visuals
    min_index = int(0.02 * len(output))
    max_index = int(0.98 * len(output)) - 1

    g_min = output[min_index]  # This is the min that we will graph
    g_max = output[max_index]  # This is the max that we will graph

    binsize = (g_max - g_min) / num_sim_bins
    bins = np.arange(g_min, g_max, binsize)
    plt.figure(figsize=(12, 8))

    plt.xlim(g_min, g_max)

    # Format the x axis so it shows normal number format with commas (not scientific notation)
    ax = plt.gca()
    ax.get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    n, arr, patches = plt.hist(output, bins=bins)
    plt.xlabel('Final value')
    plt.ylabel('count')

    ypos = n[np.argmax(n)] + 2  # Y position of the bin with the maximum count

    # These are the logical coordinates of the graph
    xmin = output[min_index]
    xmax = output[max_index]
    xlen = xmax - xmin
#    ymin = 0
#    ymax = ypos
    yinc = ypos / 31  # Determined empirically, based on font and graph size

    # Put a line for the mode and label it
    mode = arr[np.argmax(n)]
    plt.axvline(mode + binsize / 2, color='k', linestyle='dashed', linewidth=1)  # Mode
    plt.text(mode + binsize / 2 + mode / 10, ypos, 'Mode: ${0:,.0f}'.format(mode))

    # Put a line for the median and label it
    med = output[int(len(output) / 2)]
    plt.axvline(med, color='g', linestyle='dashed', linewidth=1)
    plt.text(med + xlen / 100, ypos - yinc, 'Median: ${0:,.0f}'.format(med))

    # Put a line for the average and label it
    avg = sum(output) / len(output)
    plt.axvline(avg, color='b', linestyle='dashed', linewidth=1)  # Mean
    plt.text(avg + xlen / 100, ypos - 2 * yinc, 'Average: ${0:,.0f}'.format(avg))

    xpos = xmin + 0.75 * xlen

    plt.text(xpos, ypos, 'Assumptions')
    plt.text(xpos, ypos - yinc, '-----------')
    plt.text(xpos, ypos - 2 * yinc, 'Spouse1 Ret age: {0:,.0f}'.format(s1_ret_age))
    plt.text(xpos, ypos - 3 * yinc, 'Spouse1 SS age: {0:,.0f}'.format(s1_ss_age))
    plt.text(xpos, ypos - 4 * yinc, 'Spouse1 Final ret age: {0:,.0f}'.format(s1_ret_ret_age))
    plt.text(xpos, ypos - 5 * yinc, 'Spouse1 Lifespan: {0:,.0f}'.format(s1_lifespan))
    plt.text(xpos, ypos - 6 * yinc, 'Spouse2 Ret age: {0:,.0f}'.format(s2_ret_age))
    plt.text(xpos, ypos - 7 * yinc, 'Spouse2 SS age: {0:,.0f}'.format(s2_ss_age))
    plt.text(xpos, ypos - 8 * yinc, 'Spouse2 Final ret age: {0:,.0f}'.format(s2_ret_ret_age))
    plt.text(xpos, ypos - 9 * yinc, 'Inflation mean: {0:,.4f}'.format(inflation_mean))
    plt.text(xpos, ypos - 10 * yinc, 'Inflation std dev: {0:,.4f}'.format(inflation_stddev))
    plt.text(xpos, ypos - 11 * yinc, 'Investment mean: {0:,.4f}'.format(invest_mean))
    plt.text(xpos, ypos - 12 * yinc, 'Investment std dev: {0:,.4f}'.format(invest_stddev))
    plt.text(xpos, ypos - 13 * yinc, 'Spend decay mean: {0:,.4f}'.format(spend_decay_mean))
    plt.text(xpos, ypos - 14 * yinc, 'Spend decay std dev: {0:,.4f}'.format(spend_decay_stddev))
    plt.text(xpos, ypos - 15 * yinc, 'Windfall amount: {0:,.0f}'.format(windfall_amount))
    plt.text(xpos, ypos - 17 * yinc, 'Results')
    plt.text(xpos, ypos - 18 * yinc, '-------')
    plt.text(xpos, ypos - 19 * yinc,
             'Percentage over 0: {0:,.2f}%'.format(100 * (sum(i >= 0 for i in output) / len(output))))
    plt.text(xpos, ypos - 20 * yinc, 'Minimum: {0:,.2f}%'.format(min(output)))
    plt.show()
    return


# This function is called by the RetirementFrontEnd notebook in addition to this notebook
def createresultdf(num_combos):
    # Create the dataframe that will hold the complete set of simulation results
    cols = ['s1RetAge', 's2RetAge', 's1RetRetAge', 's2RetRetAge', 's1SSAge', 's2SSAge',
            's1Lifespan', 'InflationMean', 'InflationStd', 'InvestmentMean', 'InvestmentStd', 'SpendDecayMean',
            'SpendDecayStd',
            'PercentOver0', 'Median', 'Average', 'Min', 'Max', 'SimOutput']
    df = pd.DataFrame(columns=cols, index=np.arange(0, num_combos))
    return df


# Returns a random sequence of numbers of length num that are randomly drawn from the specified normal distribution
def sim(mean, stddev, num):
    return np.random.normal(mean, stddev, num)


def do_sim(b):
    # NB: b is the button object. It is automatically passed to this function by ipywidgets

    # Number of years to simulate (e.g. "until Spouse1 is 95 years old")
    n_yrs = int(s1_ls_w.value) - s1_current_age
#    income_replacement = float(income_replacement_w.value)
    windfall = float(windfall_w.value)
    # Run the simulation with the configuration based on the UI
    run_simulation(
        int(s1_ret_age_w.value),
        int(s2_ret_age_w.value),
        int(s1_ret_ret_age_w.value),
        int(s2_ret_ret_age_w.value),
        int(s1_ss_age_w.value),
        int(s2_ss_age_w.value),
        inflation[0],
        ast.literal_eval(investment_w.value),
        spend_decay[0],
        n_yrs,
        num_exp,
        output,
        0,  # sim_num
        df,
        int(s1_ls_w.value)
    )
    #    print_assumptions_results(df.SimOutput[0],
    #                              s1_ret_age_w.value, s2_ret_age_w.value,
    #                              s1_ret_ret_age_w.value, s2_ret_ret_age_w.value,
    #                              s1_ss_age_w.value, s2_ss_age_w.value,
    #                              s1_ls_w.value,
    #                              inflation[0][0], inflation[0][1],
    #                              ast.literal_eval(investment_w.value)[0],ast.literal_eval(investment_w.value)[1])
    plot_output(df.SimOutput[0],
                float(s1_ret_age_w.value), float(s2_ret_age_w.value),
                float(s1_ret_ret_age_w.value), float(s2_ret_ret_age_w.value),
                float(s1_ss_age_w.value), float(s2_ss_age_w.value),
                float(s1_ls_w.value),
                inflation[0][0], inflation[0][1],
                ast.literal_eval(investment_w.value)[0], ast.literal_eval(investment_w.value)[1],
                spend_decay[0][0], spend_decay[0][1], windfall)

# Starting assumptions
# s1 = spouse #1, s2 = spouse #2

"""
s1_current_age = calculate_age(date(1957, 10, 18))
s1_current_income = 0  # Current income

# NB: The following lists are used when evaluating multiple scenarios.
s1_ret_age = [62, 65]  # Age of retirement from primary job
s1_ss_age = [62, 66, 70]  # Age when starting to collect SS
s1_lifespan = [75, 85, 95, 100]  # THE END

s2_current_age = calculate_age(date(1960, 2, 12))
s2_current_income = 0  # Current income
s2_ret_age = [59, 62]  # Age of retirement from primary job
s2_ss_age = [62, 66, 70]  # Age when starting to collect SS
# Assumptions about a second job in retirement
s2_sec_job = 0  # Income in second job
s2_ret_ret_age = [59, 66, 70]  # Age of retirement from primary job

s1_sec_job = 0  # Income in second job
s1_ret_ret_age = [65, 67, 70]  # Age of retirement from primary job

windfall = 4000000  # Windfall
windfall_age = 70  # Age of windfall
# Some one time, large ticket items
wedding_cost = -40000  # x4
bathroom_cost = -15000  # x3
kitchen_cost = -15000  # x1

nestegg_current = 2460000  # nestegg is updated quarterly (manually)

income_replacement = 0.50  # Percentage of our current income that we desire in retirement
drawdown = 120000  # This is the annual amount spent in retirement which is drawn from the nestegg

# Social security data per year if we wait until 62/66.5/70
s1_ss_at_62 = 25464  # at 62 years
s1_ss_at_66 = 35460  # at 66 years and 6 months
s1_ss_at_70 = 45612  # at 70

s2_ss_at_62 = 18348  # at 62
s2_ss_at_66 = 28872  # at 66 years and 6 months
s2_ss_at_70 = 37476  # at 70

cola = 1.02  # Average annual cost of living adjustment for SS

num_exp = 10000  # The number of experiments to run
num_sim_bins = 100  # Used for histogram displays

# Initialize  investment returns; S&P500 39 years mean = 9.391% (1.09391) and SD = 1.96% (0.197028)
# Inflation and investment are lists of lists. The inner list is a pair that specifies the mean and standard deviation
# The simulation will iterate through all combinations of inflation and investments
investment = [[1.09391, 0.197028],
              [(1.09391 + 1.03) / 2, 0.197028 / 2],
              [1.04, 0.01]]

# The following S&P 500 and inflation data are based on info I found on the net
# Initialize Inflation data#inflation_mean = 1.027
inflation = [[1.027, 0.011]]

# Amex reports that a typical retiree spends 2% less every year they are in retirement. Model this as a probability
# distribution with a lot of variability (1 standard deviation is 10%)
spend_decay = [[0.02, 0.001]]

# initialize the output list to zeros. Output will contain the final value of the portfolio for each experiment
output = [0 for i in range(num_exp)]

n_yrs = 0  # This variable is is calculated (later) to be the number of years in the simulation (lifespan - current age)

plt.style.use('ggplot')

# Create a dataframe that will hold the result of a single simulation
df = createresultdf(1)


style = {'description_width': 'initial', 'width': 'initial'}

s1_label_w = widgets.Label(value="Spouse 1:", style=style)
s1_ss_age_w = widgets.RadioButtons(
    options=list(map(str, s1_ss_age)),
    value='66',
    description='SS age:',
    description_tooltip='Age at which Spouse 1 will start taking Social Security',
    disabled=False,
    style=style
)
s1_ret_age_w = widgets.RadioButtons(
    options=list(map(str, s1_ret_age)),
    value='62',
    description='Retirement age:',
    description_tooltip='Age of retirement from primary job',
    disabled=False,
    style=style
)
s1_ret_ret_age_w = widgets.RadioButtons(
    options=list(map(str, s1_ret_ret_age)),
    value='65',
    description='Final Retirement Age:',
    description_tooltip='Age of retirement from secondary job',
    disabled=False,
    style=style
)
s1_ls_w = widgets.RadioButtons(
    options=list(map(str, s1_lifespan)),
    value='95',
    description='Spouse 1 lifespan:',
    description_tooltip='How long Spouse 1 expects to live',
    disabled=False,
    style=style
)

s2_label_w = widgets.Label(value="Spouse 2:", style=style)
s2_ss_age_w = widgets.RadioButtons(
    options=list(map(str, s2_ss_age)),
    value='66',
    description='SS age:',
    description_tooltip='Age at which Spouse 2 will start taking Social Security',
    disabled=False,
    style=style
)
s2_ret_age_w = widgets.RadioButtons(
    options=list(map(str, s2_ret_age)),
    value='59',
    description='Retirement age:',
    description_tooltip='Age of retirement from primary job',
    disabled=False,
    style=style
)
s2_ret_ret_age_w = widgets.RadioButtons(
    options=list(map(str, s2_ret_ret_age)),
    value='66',
    description='Final Retirement Age:',
    description_tooltip='Age of retirement from secondary job',
    disabled=False,
    style=style
)
investment_w = widgets.RadioButtons(
    options=list(map(str, investment)),
    description='Investment:',
    description_tooltip='Mean return and standard deviation of investment',
    disabled=False,
    style=style
)
income_replacement_w = widgets.FloatText(
    value=120000,
    description='Desired annual income:',
    description_tooltip='Desired income replacement as an absolute value',
    disabled=False,
    style=style
)
windfall_w = widgets.FloatText(
    value=4000000,
    description='Windfall:',
    description_tooltip='Windfall',
    disabled=False,
    style=style
)
windfall_age_w = widgets.IntText(
    value=67,
    description='Windfall age:',
    description_tooltip='Windfall age',
    disabled=False,
    style=style
)

run_sim_w = widgets.Button(
    description='Run Simulation',
    disabled=False,
    button_style='',  # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Click me',
    icon='check'
)
row1 = HBox([s1_label_w, s1_ret_age_w, s1_ret_ret_age_w, s1_ss_age_w])
row2 = HBox([s2_label_w, s2_ret_age_w, s2_ret_ret_age_w, s2_ss_age_w])
row3 = HBox([s1_ls_w, investment_w])
row4 = HBox([income_replacement_w])
row5 = HBox([windfall_age_w, windfall_w])
v = VBox([row1, row2, row3, row4, row5])
display(v, run_sim_w)
run_sim_w.on_click(do_sim)
"""