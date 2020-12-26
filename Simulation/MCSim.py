import numpy as np
from Simulation.users.utils import calculate_age
from Simulation.asset_classes.forms import getAssetClass


# Returns a random sequence of numbers of length num that are randomly drawn from the specified normal distribution
def sim(mean, stddev, num):
    return np.random.normal(mean, stddev, num)


def run_simulation(scenario, sim_data):
    # Number of years to simulate
    if scenario.has_spouse:
        n_yrs = max(scenario.lifespan_age - scenario.current_age, scenario.s_lifespan_age - scenario.s_current_age)
    else:
        n_yrs = scenario.lifespan_age - scenario.current_age

    # These are numpy.ndarrays which hold the simulation results
    # fd_output[year][experiment]
    fd_output = np.zeros((n_yrs, sim_data.num_exp))  # Final distribution output
    dd_output = np.zeros((n_yrs, sim_data.num_exp))  # Drawdown output
    ss_output = np.zeros((n_yrs, sim_data.num_exp))  # Social security output
    sss_output = np.zeros((n_yrs, sim_data.num_exp)) # Spouse's social security output
    inv_output = np.zeros((n_yrs, sim_data.num_exp))  # Spouse's social security output
    inf_output = np.zeros((n_yrs, sim_data.num_exp))  # Spouse's social security output
    sd_output = np.zeros((n_yrs, sim_data.num_exp))  # Spouse's social security output
    cola_output = np.zeros((n_yrs, sim_data.num_exp))  # Spouse's social security output
    p0_output = np.zeros((n_yrs))  # Percent over zero

    # Run the simulation with the investment configuration based on the UI
    asset_class = getAssetClass(scenario.asset_class_id)
    invest_avg = asset_class.avg_ret
    invest_std_dev = asset_class.std_dev

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

        if s1_age >= scenario.retirement_age:
            drawdown = scenario.drawdown
        else:
            drawdown = 0

        # Generate a random sequence of investment annual returns based on a normal distribution
        s_invest = sim(invest_avg, invest_std_dev, n_yrs)

        # Generate a random sequence of annual inflation rates using a normal distribution
        s_inflation = sim(sim_data.inflation[0], sim_data.inflation[1], n_yrs)

        # Generate a random sequence of annual spend decay
        s_spend_decay = sim(sim_data.spend_decay[0], sim_data.spend_decay[1], n_yrs)

        # Generate a random sequence of social security cost of living increases
        cola = sim(sim_data.cola[0], sim_data.cola[1], n_yrs)

        for year in range(n_yrs):
            fd_output[year][experiment] = nestegg  # Record the results
            dd_output[year][experiment] = drawdown
            inv_output[year][experiment] = s_invest[year]
            inf_output[year][experiment] = s_inflation[year]
            sd_output[year][experiment] = s_spend_decay[year]
            cola_output[year][experiment] = cola[year]

            s1_age += 1
            if scenario.has_spouse:
                s2_age += 1

            # Calculate the primary user's new salary, nestegg and drawdown amount
            if s1_age < scenario.retirement_age:            # Working
                nestegg += s1_income * scenario.savings_rate
                s1_income *= s_inflation[year]

            elif s1_age == scenario.retirement_age:         # Year of retirement
                s1_income = scenario.ret_income
                drawdown = scenario.drawdown
                nestegg -= drawdown
                nestegg += s1_income

            elif s1_age < scenario.ret_job_ret_age:         # Partially retired
                drawdown *= s_inflation[year]
                drawdown *= (1.0 - s_spend_decay[year])
                nestegg -= drawdown
                nestegg += s1_income
                s1_income *= s_inflation[year]
            else:                                           # Fully retired
                s1_income = 0
                drawdown *= s_inflation[year]
                drawdown *= (1.0 - s_spend_decay[year])
                nestegg -= drawdown

            # For spouse, just adjust the income
            if scenario.has_spouse:
                if s2_age < scenario.s_retirement_age:  # Working
                    nestegg += s2_income * scenario.s_savings_rate
                    s2_income *= s_inflation[year]
                elif s2_age == scenario.s_retirement_age:  # Year of retirement
                    nestegg += s2_income
                    s2_income = scenario.s_ret_income
                elif s2_age < scenario.s_ret_job_ret_age:  # Partially retired
                    nestegg += s2_income
                    s2_income *= s_inflation[year]
                else:  # Fully retired
                    s2_income = 0


            # Add windfall to the nestegg
            if s1_age == scenario.windfall_age:
                nestegg += scenario.windfall_amount

            # Add SS to the nestegg
            if s1_age == s1ssa_sim:
                s1ss = scenario.ss_amount
                ss_output[year][experiment] = s1ss
                nestegg += s1ss
            if s1_age > s1ssa_sim:
                s1ss *= (1+cola[year])
                ss_output[year][experiment] = s1ss
                nestegg += s1ss


            # Add spouse's SS to the nestegg
            if scenario.has_spouse:
                if s2_age == s2ssa_sim:
                    s2ss = scenario.s_ss_amount
                    sss_output[year][experiment] = s2ss
                    nestegg += s2ss
                if s2_age > s2ssa_sim:
                    s2ss *= (1+cola[year])
                    sss_output[year][experiment] = s2ss
                    nestegg += s2ss

            # Grow the nestegg
            nestegg *= (1+s_invest[year])

            if (s1_age > scenario.ret_job_ret_age) and (nestegg < 0):
                nestegg = 0.0

    for year in range(n_yrs):
        # Calculate the percentage of results over zero
        p0_output[year] = 100 * (sum(i > 0.0 for i in fd_output[year]) / sim_data.num_exp)
    return p0_output, fd_output, dd_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output


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
