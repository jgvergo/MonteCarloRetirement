from flask import render_template, url_for, flash, redirect, request, abort, Blueprint, Response
from flask_login import current_user, login_required
from Simulation import db
from Simulation.extensions import redis_conn
from Simulation.scenarios.forms import ScenarioForm, DisplaySimResultForm, DisplayAllSimResultForm
from Simulation.utils import populate_investment_dropdown, get_investment_from_select_field, get_asset_mix
from Simulation.models import Scenario, SimData, SimReturnData
from Simulation.utils import calculate_age
from Simulation.MCSim import run_sim_background, run_all_sim_background
from Simulation.MCGraphs import plot_graphs
from datetime import date
import pandas as pd
import time
import json
from rq.job import Job


scenarios = Blueprint('scenarios', __name__)


@scenarios.route("/scenario/new", methods=['GET', 'POST'])
@login_required
def new_scenario(titles=None):
    # User has clicked on "New Scenario" or has clicked "Save" after filling out a blank form or has clicked "Save and
    # Run" after filling out a blank form
    form = ScenarioForm()
    populate_investment_dropdown(form.investment, kind='AssetMix')

    if form.validate_on_submit():
        scenario = Scenario()
        scenario.user_id = current_user.id

        copy_form_2_scenario(form, scenario)

        db.session.add(scenario)
        db.session.commit()
        flash('Your scenario has been created!', 'success')

        if form.submit.data:
            flash('Your scenario has been updated!', 'success')
            return redirect(url_for('main.home'))

    # If we get here, the user has selected "New Scenario" and we are rendering a form with no data
    return render_template('create_scenario.html', title='New Scenario',
                           form=form, legend='New Scenario')


@scenarios.route("/scenario/<int:scenario_id>", methods=['GET', 'POST'])
def scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    return render_template('scenario.html', title=scenario.title, scenario=scenario)


@scenarios.route("/scenario/<int:scenario_id>/update", methods=['GET', 'POST'])
@login_required
def update_scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    if scenario.author != current_user:
        abort(403)
    form = ScenarioForm()
    if form.validate_on_submit():
        if form.submit.data:
            # Copy the info from the form to a Scenario object and save it to the DB
            copy_form_2_scenario(form, scenario)
            db.session.commit()
            flash('Your scenario has been updated', 'success')
            return redirect(url_for('scenarios.scenario', scenario_id=scenario.id))
        elif form.cancel.data:
            flash('Changes to your scenario have been discarded', 'success')
            return redirect(url_for('scenarios.scenario', scenario_id=scenario.id))
    elif request.method == 'GET':
        copy_scenario_2_form(scenario, form)

        populate_investment_dropdown(form.investment, scenario.asset_mix_id, kind='AssetMix')

    return render_template('create_scenario.html', title='Update Scenario',
                           form=form, legend='Update Scenario')


@scenarios.route("/scenario/<int:scenario_id>/delete", methods=['POST'])
@login_required
def delete_scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    if scenario.author != current_user:
        abort(403)
    db.session.delete(scenario)
    db.session.commit()
    flash('Your scenario has been deleted!', 'success')
    return redirect(url_for('main.home'))


@scenarios.route("/scenario/<int:scenario_id>/run", methods=['GET', 'POST'])
@login_required
def run_scenario(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    if scenario.author != current_user:
        abort(403)

    job_id = run_sim_background(scenario, True)
    return {'job_id': job_id}


@scenarios.route("/scenario/<int:scenario_id>/run_all", methods=['GET', 'POST'])
@login_required
def run_all(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    if scenario.author != current_user:
        abort(403)

    job = q.enqueue(run_all_sim_background(scenario, True))

    if SimData().debug:
        registry = FailedJobRegistry(queue=q)

        # Show all failed job IDs and the exceptions they caused during runtime
        for job_id in registry.get_job_ids():
            job = Job.fetch(job_id, connection=redis_conn)
            print(job_id, job.exc_info)


    return redirect(url_for('main.home'))


@scenarios.route('/progress/<string:job_id>')
def progress(job_id):
    def get_status():

        job = Job.fetch(job_id, connection=redis_conn)
        status = job.get_status()

        while status != 'finished':

            status = job.get_status()
            job.refresh()

            d = {'status': status}

            if 'progress' in job.meta:
                d['value'] = job.meta['progress']
            else:
                d['value'] = 0

            # IF there's a result, add this to the stream
            if job.result:
                d['result'] = job.result

            json_data = json.dumps(d)
            yield f"data:{json_data}\n\n"
            time.sleep(0.2)
    return Response(get_status(), mimetype='text/event-stream')


@scenarios.route("/scenario/<string:job_id>/display_result", methods=['GET', 'POST'])
@login_required
def display_result(job_id):
    sd = SimData.query.first()
    srd = SimReturnData.query.filter_by(job_id=job_id).first()
    scenario = Scenario.query.get_or_404(srd.scenario_id)
    if scenario.author != current_user:
        abort(403)

    plot_urls = plot_graphs(srd.fd_output, srd.rs_output, srd.ss_output, srd.sss_output,
                            srd.inv_output, srd.inf_output, srd.sd_output, srd.cola_output, srd.p0_output)

    form = DisplaySimResultForm()
    form.title.data = scenario.title
    asset_mix = get_asset_mix(scenario.asset_mix_id)
    nl = '\n'
    form.taf.data = 'Asset mix name: {}{}' \
                    'Number of Monte Carlo experiments: {:,}'. \
        format(asset_mix.title, nl, sd.num_exp)

    return render_template('display_sim_result.html', title='Simulated Scenario',
                           form=form, legend='Simulated Scenario', plot_urls=plot_urls)
@scenarios.route("/scenario/<string:job_id>/display_all_result", methods=['GET', 'POST'])
@login_required
def display_all_result(job_id):
    srd = SimReturnData.query.filter_by(job_id=job_id).first()
    scenario = Scenario.query.get_or_404(srd.scenario_id)
    if scenario.author != current_user:
        abort(403)
    form = DisplayAllSimResultForm()
    return render_template('display_all_sim_result.html', title='Simulated Scenario',
                           form=form, legend='Simulated Scenario')


def copy_scenario_2_form(s, form):
    form.title.data = s.title
    form.birthdate.data = s.birthdate
    form.s_birthdate.data = s.s_birthdate

    form.current_income.data = s.current_income
    form.s_current_income.data = s.s_current_income

    form.savings_rate.data = s.savings_rate
    form.s_savings_rate.data = s.s_savings_rate

    form.ss_date.data = s.ss_date
    form.s_ss_date.data = s.s_ss_date

    form.ss_amount.data = s.ss_amount
    form.s_ss_amount.data = s.s_ss_amount

    form.retirement_age.data = s.retirement_age
    form.s_retirement_age.data = s.s_retirement_age

    form.ret_income.data = s.ret_income
    form.s_ret_income.data = s.s_ret_income

    form.ret_job_ret_age.data = s.ret_job_ret_age
    form.s_ret_job_ret_age.data = s.s_ret_job_ret_age

    form.lifespan_age.data = s.lifespan_age
    form.s_lifespan_age.data = s.s_lifespan_age

    form.windfall_amount.data = s.windfall_amount
    form.windfall_age.data = s.windfall_age

    form.nestegg.data = s.nestegg
    form.ret_spend.data = s.ret_spend
    form.has_spouse.data = s.has_spouse
    return


def copy_form_2_scenario(form, s):
    s.title = form.title.data

    s.birthdate = form.birthdate.data
    s.s_birthdate = form.s_birthdate.data

    s.current_income = form.current_income.data
    s.s_current_income = form.s_current_income.data

    s.savings_rate = form.savings_rate.data
    s.s_savings_rate = form.s_savings_rate.data

    s.ss_date = form.ss_date.data
    s.s_ss_date = form.s_ss_date.data

    s.ss_amount = form.ss_amount.data
    s.s_ss_amount = form.s_ss_amount.data

    s.retirement_age = form.retirement_age.data
    s.s_retirement_age = form.s_retirement_age.data

    s.ret_income = form.ret_income.data
    s.s_ret_income = form.s_ret_income.data

    s.ret_job_ret_age = form.ret_job_ret_age.data
    s.s_ret_job_ret_age = form.s_ret_job_ret_age.data

    s.lifespan_age = form.lifespan_age.data
    s.s_lifespan_age = form.s_lifespan_age.data

    s.windfall_amount = form.windfall_amount.data
    s.windfall_age = form.windfall_age.data

    s.has_spouse = form.has_spouse.data
    s.nestegg = form.nestegg.data
    s.ret_spend = form.ret_spend.data

    # Calculate ages from birthdates and save the,
    s.current_age = calculate_age(date.today(), form.birthdate.data)
    if s.has_spouse:
        s.s_current_age = calculate_age(date.today(), form.s_birthdate.data)

    asset_mix_id, asset_mix = get_investment_from_select_field(form.investment)
    s.asset_mix_id = asset_mix_id
    return
