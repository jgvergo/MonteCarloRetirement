from os import abort
import numpy as np
import pandas as pd
from Simulation.utils import calculate_age
from Simulation.utils import get_invest_data
from Simulation.models import SimData, AssetMix, AssetClass
from Simulation.extensions import q, redis_conn
from rq.registry import FailedJobRegistry, Job


class RunSimParams():
    def __init__(self):
        self.scenario = None
        self.investments = None
        self.sd = None
        self.num_sims = None
        self.sim_num = None

        # Title and type used for "Run All"
        self.title = None
        self.type = None

    def __str__(self):
        return " % s,  % s" % (self.title, self.type)


def run_sim_background(scenario, assetmix):
    sd = SimData.query.first()

    rsp = RunSimParams()
    rsp.scenario = scenario
    rsp.sd = sd
    rsp.num_sims = 1
    rsp.sim_num = 0
    rsp.investments = get_invest_data(scenario.asset_mix_id, assetmix)
    rsp_list = []
    rsp_list.append(rsp)
    job = q.enqueue(_run_sim_background, rsp_list, job_timeout=6000)

    if sd.debug:
        registry = FailedJobRegistry(queue=q)

        # Show all failed job IDs and the exceptions they caused during runtime
        for job_id in registry.get_job_ids():
            job = Job.fetch(job_id, connection=redis_conn)
            print(job_id, job.exc_info)

    return job.id


# This routine (and any called routine from the routine) run as part of the Worker.py process
def _run_sim_background(rsp_list):
    from rq import get_current_job
    rsp = rsp_list[0]
    job = get_current_job()
    rsp.job = job
    if rsp.sd.debug:
        p0_output, fd_output, rs_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output = \
            _run_simulation(rsp)

        return rsp.scenario, p0_output, fd_output, rs_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output

    else:
        p0_output, fd_output, rs_output, ss_output, sss_output, = _run_simulation(rsp)

        return rsp.scenario, p0_output, fd_output, rs_output, ss_output, sss_output


def run_all_sim_background(scenario, assetmix):
    sd = SimData.query.first()

    # Build the list of run_simulation parameters
    num_sims = len(AssetMix.query.all()) + len(AssetClass.query.all())
    rsp_list = []
    sim_num = 0

    # First do the AssetMixes
    asset_mix_list = AssetMix.query.order_by(AssetMix.title.asc()).all()
    for i, asset_mix in enumerate(asset_mix_list):
        scenario.asset_mix_id = asset_mix.id
        rsp = RunSimParams()
        rsp.sim_num = sim_num
        rsp.investments = get_invest_data(scenario.asset_mix_id, assetmix)
        rsp.type = 'Asset Mix'
        rsp.title = asset_mix.title

        # Only need to pass one sd,scenario and num_sims since they are all identical
        if sim_num == 0:
            rsp.scenario = scenario
            rsp.num_sims = num_sims
            rsp.sd = sd

        rsp_list.append(rsp)
        sim_num += 1

    # ...then do the AssetClasses
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc()).all()
    for j, asset_class in enumerate(asset_class_list):
        scenario.asset_mix_id = asset_class.id
        rsp = RunSimParams()
        rsp.sim_num = sim_num
        rsp.investments = get_invest_data(scenario.asset_mix_id, assetmix)
        rsp.type = 'Asset Class'
        rsp.title = asset_class.title

        rsp_list.append(rsp)
        sim_num += 1

    job = q.enqueue(_run_all_sim_background, rsp_list, job_timeout=6000)

    if sd.debug:
        registry = FailedJobRegistry(queue=q)

        # Show all failed job IDs and the exceptions they caused during runtime
        for job_id in registry.get_job_ids():
            job = Job.fetch(job_id, connection=redis_conn)
            print(job_id, job.exc_info)

    return job.id


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
        df.loc[i] = [rsp.title, rsp.type, p0_output[year], fd_output[year][int(rsp_list[0].sd.num_exp / 2)]]

    return rsp_list[0].scenario, df


# Returns a random sequence of numbers of length num that are randomly drawn from the specified normal distribution
def sim(mean, stddev, num):
    return np.random.normal(mean, stddev, num)


def _run_simulation(rsp):
    from rq import get_current_job

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
        inv_output = np.zeros((n_yrs, sd.num_exp))  # Investments output
        inf_output = np.zeros((n_yrs, sd.num_exp))  # Inflation output
        sd_output = np.zeros((n_yrs, sd.num_exp))  # Spend decay output
        cola_output = np.zeros((n_yrs, sd.num_exp))  # Cost of living output

    # Calculate the age at which each spouse will take social security
    s1ssa_sim = calculate_age(scenario.ss_date, scenario.birthdate)
    if scenario.has_spouse:
        s2ssa_sim = calculate_age(scenario.s_ss_date, scenario.s_birthdate)

    # Run the experiments
    for experiment in range(sd.num_exp):

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

        # Set the initial social security amount to 0.
        s1ss = 0
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

        for year in range(n_yrs):
            fd_output[year][experiment] = nestegg  # Record the results
            rs_output[year][experiment] = ret_spend

            if sd.debug:
                # inv_output is calculated and recorded when nestegg is calculated, below
                inf_output[year][experiment] = s_inflation[year]
                sd_output[year][experiment] = s_spend_decay[year]
                cola_output[year][experiment] = cola[year]
            s1_age += 1
            if scenario.has_spouse:
                s2_age += 1

            # Calculate the primary user's new salary, nestegg and ret_spend amount
            if s1_age < scenario.retirement_age:            # Working
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

            # Grow the nestegg, but first save the value so the same value can be used for all investments
            tmp_ne = nestegg
            for inv in s_invest:
                growth = (tmp_ne * inv[0]/100) * (inv[1][year])
                nestegg += growth
                # The investment return for this year/experiment is the weighted sum of the asset class returns
                # times the percentage of the portfolio invested in the asset class
                if sd.debug:
                    inv_output[year][experiment] += (inv[0]/100) * (inv[1][year])

            if (s1_age > scenario.ret_job_ret_age) and (nestegg < 0):
                nestegg = 0.0

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
