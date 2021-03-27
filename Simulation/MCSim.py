from Simulation.utils import get_invest_data
from Simulation.models import SimData, AssetMix, AssetClass
from Simulation.extensions import q, redis_conn
from Simulation.BackgroundSim import _run_sim_background, _run_all_sim_background
from rq.registry import FailedJobRegistry, Job
import os


# The convention I adopted in this file is that any function name that starts with an underscore ("_") is run in a
# worker process

# This object is passed from the web process to the background (worker) process. It contains all the information
# necessary to do a run or run all simulation
class RunSimParams:
    def __init__(self):
        self.scenario = None
        self.investments = None
        self.sd = None
        self.num_sims = None
        self.sim_num = None

        # Title and type used for "Run All"
        self.investment_title = None
        self.investment_type = None

    def __str__(self):
        return " %s,  %s, %d, %d" % (self.investment_title, self.investment_type, self.num_sims, self.sim_num)


def run_sim_background(scenario):
    sd = SimData.query.first()
    sd.num_exp = int(int(os.getenv("MCR_RUN_NUM_EXP", 5000)))

    rsp = RunSimParams()
    rsp.scenario = scenario
    rsp.sd = sd
    rsp.num_sims = 1
    rsp.sim_num = 0
    rsp.investments = get_invest_data(scenario.asset_mix_id, True)
    rsp.investment_title = 'N/A'
    rsp.investment_type = 'N/A'
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


def run_all_sim_background(scenario):
    sd = SimData.query.first()
    sd.num_exp = int(int(os.getenv("MCR_RUNALL_NUM_EXP", 5000)))

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
        rsp.investments = get_invest_data(scenario.asset_mix_id, True)
        rsp.investment_type = 'Asset Mix'
        rsp.investment_title = asset_mix.title

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
        rsp.investments = get_invest_data(scenario.asset_mix_id, False)
        rsp.investment_type = 'Asset Class'
        rsp.investment_title = asset_class.title

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
