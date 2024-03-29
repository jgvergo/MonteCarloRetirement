import numpy as np
import pandas as pd
from Simulation.utils import calculate_age
from rq import get_current_job


# This routine (and any called routine from the routine) run as part of the Worker.py process
def _run_sim_background(rsp_list):
    rsp = rsp_list[0]
    job = get_current_job()
    rsp.job = job
    if rsp.sd.debug:
        p0_output, fd_output, rs_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output = \
            _run_simulation(rsp)
        p0_output.tofile('p0_output.bin')
        fd_output.tofile('fd_output.bin')
        rs_output.tofile('rs_output.bin')
        ss_output.tofile('ss_output.bin')
        sss_output.tofile('sss_output.bin')
        inv_output.tofile('inv_output.bin')
        inf_output.tofile('inf_output.bin')
        sd_output.tofile('sd_output.bin')
        cola_output.tofile('cola_output.bin')

        return rsp.scenario

    else:
        p0_output, fd_output, rs_output, ss_output, sss_output, = _run_simulation(rsp)
        p0_output.tofile('p0_output.bin')
        fd_output.tofile('fd_output.bin')
        rs_output.tofile('rs_output.bin')
        ss_output.tofile('ss_output.bin')
        sss_output.tofile('sss_output.bin')
        return rsp.scenario


# This runs in an rq worker background process
def _run_all_sim_background(rsp_list):

    # Initialize a blank dataframe
    column_names = ['Title', 'Type', 'P0', '50th % Final Nestegg']
    df = pd.DataFrame(columns=column_names)

    for i, rsp in enumerate(rsp_list):
        rsp.sd = rsp_list[0].sd
        rsp.scenario = rsp_list[0].scenario
        rsp.num_sims = rsp_list[0].num_sims

        p0_output, fd_output = _run_simulation(rsp)
        year = p0_output.shape[0] - 1
        fd_output[year].sort()
        df.loc[i] = [rsp.investment_title, rsp.investment_type, p0_output[year], fd_output[year][int(rsp_list[0].sd.num_exp / 2)]]
    df.to_csv('RunAll.csv')
    return rsp_list[0].scenario


# Returns a random sequence of numbers of length num that are randomly drawn from the specified normal distribution
def sim(mean, stddev, num):
    return np.random.normal(mean, stddev, num)


def _run_simulation(rsp):
    job = get_current_job()

    # Unpack the parameters
    scenario = rsp.scenario
    sd = rsp.sd
    investments = rsp.investments
    num_sims = rsp.num_sims
    sim_num = rsp.sim_num

    # Number of years to simulate
    if scenario.has_spouse:
        n_yrs = max(scenario.lifespan_age - scenario.current_age, scenario.s_lifespan_age - scenario.s_current_age)
    else:
        n_yrs = scenario.lifespan_age - scenario.current_age

    # These are numpy.ndarrays which hold the simulation results
    fd_output = np.zeros((n_yrs, sd.num_exp))  # Final distribution output
    rs_output = np.zeros((n_yrs, sd.num_exp))  # Retirement spend output
    ss_output = np.zeros((n_yrs, sd.num_exp))  # Social security output
    sss_output = np.zeros((n_yrs, sd.num_exp))  # Spouse's social security output
    p0_output = np.zeros(n_yrs)  # Percent over zero output
    if sd.debug:
        inv_output = np.zeros((n_yrs-1, sd.num_exp))  # Investments output
        inf_output = np.zeros((n_yrs-1, sd.num_exp))  # Inflation output
        sd_output = np.zeros((n_yrs-1, sd.num_exp))  # Spend decay output
        cola_output = np.zeros((n_yrs-1, sd.num_exp))  # Cost of living output

    # Calculate the age at which each spouse will take social security
    s1ssa_sim = calculate_age(scenario.ss_date, scenario.birthdate)
    if scenario.has_spouse:
        s2ssa_sim = calculate_age(scenario.s_ss_date, scenario.s_birthdate)

    # Run the experiments
    for experiment in range(sd.num_exp):
        # Update the progress bar in the main process
        job.meta['progress'] = round(100.0 * ((sim_num/num_sims) + (experiment / sd.num_exp)/num_sims), 1)
        job.save_meta()

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

        # Set the initial social security amount.
        if s1_age >= s1ssa_sim:
            s1ss = scenario.ss_amount
        else:
            s1ss = 0
        if s2_age >= s2ssa_sim:
            s2ss = scenario.s_ss_amount
        else:
            s2ss = 0

        nestegg = scenario.nestegg

        if s1_age >= scenario.retirement_age:
            ret_spend = scenario.ret_spend
        else:
            ret_spend = 0

        # Generate a random sequences of investment annual returns based on a normal distribution and
        # also save the percentage for convenience
        ndf = pd.DataFrame(np.random.default_rng().multivariate_normal(sd.mean.values, sd.cov, size=n_yrs, check_valid='warn'))
        ndf.columns = sd.ac_df.columns
        s_invest = []
        for inv in investments:
            foo = ndf[inv[0]]
            s_invest.append([inv[1], foo])

        # Generate a random sequence of annual inflation rates using a normal distribution
        s_inflation = ndf['Inflation']

        # Generate a random sequence of annual spend decay
        s_spend_decay = sim(sd.spend_decay[0], sd.spend_decay[1], n_yrs)

        # Generate a random sequence of social security cost of living increases
        cola = sim(sd.cola[0], sd.cola[1], n_yrs)

        # Start off with the value provided by the user for the current ("zeroith") year
        fd_output[0][experiment] = nestegg
        rs_output[0][experiment] = ret_spend
        ss_output[0][experiment] = s1ss
        sss_output[0][experiment] = s2ss
        for year in range(1, n_yrs):
            s1_age += 1
            if scenario.has_spouse:
                s2_age += 1

            # Calculate the primary user's new salary, nestegg and ret_spend amount
            if s1_age < scenario.retirement_age:            # Still working
                nestegg += s1_income * scenario.savings_rate
                s1_income *= s_inflation[year]

            elif s1_age == scenario.retirement_age:         # Year of retirement
                s1_income = scenario.ret_income
                ret_spend = scenario.ret_spend
                nestegg -= ret_spend
                nestegg += s1_income

            elif s1_age < scenario.ret_job_ret_age:         # Partially retired
                ret_spend *= s_inflation[year]
                ret_spend *= (1.0 - s_spend_decay[year])
                nestegg -= ret_spend
                nestegg += s1_income
                s1_income *= s_inflation[year]
            else:                                           # Fully retired
                s1_income = 0
                ret_spend *= s_inflation[year]
                ret_spend *= (1.0 - s_spend_decay[year])
                nestegg -= ret_spend

            # For spouse, just adjust the nestegg and income
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

            # Grow the nestegg, but first save the value so the same value can be used for all investments
            tmp_ne = nestegg
            for inv in s_invest:
                growth = (tmp_ne * inv[0]/100) * (inv[1][year])
                nestegg += growth
                # The investment return for this year/experiment is the weighted sum of the asset class returns
                # times the percentage of the portfolio invested in the asset class
                if sd.debug:
                    inv_output[year-1][experiment] += (inv[0]/100) * (inv[1][year-1])

            if (s1_age > scenario.retirement_age) and (nestegg < 0):
                nestegg = 0.0

            # Save all the calculated values
            fd_output[year][experiment] = nestegg  # Record the results
            rs_output[year][experiment] = ret_spend
            ss_output[year][experiment] = s1ss
            sss_output[year][experiment] = s2ss

            if sd.debug:
                # inv_output is calculated and recorded when nestegg is calculated, below
                inf_output[year-1][experiment] = s_inflation[year]
                sd_output[year-1][experiment] = s_spend_decay[year]
                cola_output[year-1][experiment] = cola[year]

    for year in range(n_yrs):
        # Calculate the percentage of results over zero
        p0_output[year] = 100 * (sum(i > 0.0 for i in fd_output[year]) / sd.num_exp)

    if num_sims > 1:
        return p0_output, fd_output
    else:
        if sd.debug:
            return p0_output, fd_output, rs_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output
        else:
            return p0_output, fd_output, rs_output, ss_output, sss_output
