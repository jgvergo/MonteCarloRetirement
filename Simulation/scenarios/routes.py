from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from flask_login import current_user, login_required
from Simulation import db
from Simulation.scenarios.forms import ScenarioForm, DisplaySimResultForm
from Simulation.utils import populate_investment_dropdown, get_investment_from_select_field, get_asset_mix
from Simulation.models import Scenario, AssetMix, AssetClass, SimData
from Simulation.utils import calculate_age
from Simulation.MCSim import run_simulation
from Simulation.MCGraphs import plot_graphs
from datetime import date
import pandas as pd

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

        copyForm2Scenario(form, scenario)

        db.session.add(scenario)
        db.session.commit()
        flash('Your scenario has been created!', 'success')

        if form.submit.data:
            flash('Your scenario has been updated!', 'success')
            return redirect(url_for('main.home'))
        elif form.submitrun.data:
            return redirect(url_for('scenarios.run_scenario', scenario_id=scenario.id))

    # If we get here, the user has selected "New Scenario" and we are rendering a from with no data
    return render_template('create_scenario.html', title='New Scenario',
                           form=form, legend='New Scenario')


@scenarios.route("/scenario/<int:scenario_id>")
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
        # Copy the info from the form to a Scenario object and save it to the DB
        copyForm2Scenario(form, scenario)

        db.session.commit()

        if form.submit.data:
            flash('Your scenario has been updated!', 'success')
            return redirect(url_for('scenarios.scenario', scenario_id=scenario.id))
        elif form.submitrun.data:
            return redirect(url_for('scenarios.run_scenario', scenario_id=scenario.id))

    elif request.method == 'GET':
        copyScenario2Form(scenario, form)

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
    sd = SimData.query.first()
    if scenario.author != current_user:
        abort(403)

    form = DisplaySimResultForm()

    if form.validate_on_submit():
        form = ScenarioForm()
        form.id = scenario_id
        copyScenario2Form(scenario, form)
        return redirect(url_for('scenarios.update_scenario', scenario_id=scenario.id))
    else:
        # Do the simulation
        p0_output, fd_output, dd_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output = run_simulation(scenario, True)

        plot_urls = plot_graphs(fd_output, dd_output, ss_output, sss_output,
                                inv_output, inf_output, sd_output, cola_output, p0_output)

        form.title.data = scenario.title
        asset_mix = get_asset_mix(scenario.asset_mix_id)
        nl = '\n'
        form.taf.data = 'Percent over zero after {} years: {:>.2f}%{}'\
                        'Primary user age: {}{}'\
                        "Spouse's age: {}{}"\
                        'Starting nestegg: {:,}{}'\
                        'Windfall amount: {:,}{}'\
                        'Windfall age: {}{}'\
                        'Social security amount(primary user): {:,}{}'\
                        'Social security date(primary user): {}{}'\
                        'Social security amount(spouse): {:,}{}'\
                        'Social security date(spouse): {}{}'\
                        'Asset mix name: {}{}'\
                        'Number of Monte Carlo experiments: {:,}{}'\
                        'Inflation mean: {:.2f}%{}'\
                        'Inflation Standard Deviation:{:.2f}%{}'\
                        'Spend decay: {:.2f}%'.\
            format(p0_output.shape[0], p0_output[p0_output.shape[0]-1], nl,
                   scenario.current_age, nl,
                   scenario.s_current_age, nl,
                   scenario.nestegg, nl,
                   scenario.windfall_amount, nl,
                   scenario.windfall_age, nl,
                   scenario.ss_amount, nl,
                   scenario.ss_date, nl,
                   scenario.s_ss_amount, nl,
                   scenario.s_ss_date, nl,
                   asset_mix.title, nl,
                   sd.num_exp, nl,
                   100*(sd.inflation[0]-1), nl,
                   100*sd.inflation[1], nl,
                   100*sd.spend_decay[0],50)


        return render_template('display_sim_result.html', title='Simulated Scenario',
                               form=form, legend='Simulated Scenario', plot_urls=plot_urls)

@scenarios.route("/scenario/<int:scenario_id>/run_all", methods=['GET', 'POST'])
@login_required
def run_all(scenario_id):
    scenario = Scenario.query.get_or_404(scenario_id)
    sd = SimData.query.first()
    if scenario.author != current_user:
        abort(403)

    column_names = ['AssetMix Title', 'Type', 'P0', '50th % Final Nestegg']
    df = pd.DataFrame(columns=column_names)

    # First do the AssetMixes
    asset_mix_list = AssetMix.query.order_by(AssetMix.title.asc()).all()
    for i, asset_mix in enumerate(asset_mix_list):
        print(i, '/', len(asset_mix_list))  # Do the simulations
        scenario.asset_mix_id = asset_mix.id
        p0_output, fd_output, dd_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output = \
            run_simulation(scenario, assetmix=True)

        year = p0_output.shape[0]-1
        fd_output[year].sort()
        df.loc[i] = [asset_mix.title, 'Asset Mix', p0_output[year], fd_output[year][int(sd.num_exp / 2)]]

    # ...then do the AssetClasses
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc()).all()
    for j, asset_class in enumerate(asset_class_list):
        print(j, '/', len(asset_class_list))
        scenario.asset_mix_id = asset_class.id
        p0_output, fd_output, dd_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output = \
            run_simulation(scenario, assetmix=False)

        year = p0_output.shape[0] - 1
        fd_output[year].sort()
        df.loc[i+j+1] = [asset_class.title, 'Asset Class', p0_output[year], fd_output[year][int(sd.num_exp / 2)]]

    # Save it
    df.to_csv('output.csv')
    return redirect(url_for('main.home'))


def copyScenario2Form(scenario, form):
    form.title.data = scenario.title
    form.birthdate.data = scenario.birthdate
    form.s_birthdate.data = scenario.s_birthdate

    form.current_income.data = scenario.current_income
    form.s_current_income.data = scenario.s_current_income

    form.savings_rate.data = scenario.savings_rate
    form.s_savings_rate.data = scenario.s_savings_rate

    form.ss_date.data = scenario.ss_date
    form.s_ss_date.data = scenario.s_ss_date

    form.ss_amount.data = scenario.ss_amount
    form.s_ss_amount.data = scenario.s_ss_amount

    form.retirement_age.data = scenario.retirement_age
    form.s_retirement_age.data = scenario.s_retirement_age

    form.ret_income.data = scenario.ret_income
    form.s_ret_income.data = scenario.s_ret_income

    form.ret_job_ret_age.data = scenario.ret_job_ret_age
    form.s_ret_job_ret_age.data = scenario.s_ret_job_ret_age

    form.lifespan_age.data = scenario.lifespan_age
    form.s_lifespan_age.data = scenario.s_lifespan_age

    form.windfall_amount.data = scenario.windfall_amount
    form.windfall_age.data = scenario.windfall_age

    form.nestegg.data = scenario.nestegg
    form.drawdown.data = scenario.drawdown
    form.has_spouse.data = scenario.has_spouse
    return

def copyForm2Scenario(form, scenario):
    scenario.title = form.title.data

    scenario.birthdate = form.birthdate.data
    scenario.s_birthdate = form.s_birthdate.data

    scenario.current_income = form.current_income.data
    scenario.s_current_income = form.s_current_income.data

    scenario.savings_rate = form.savings_rate.data
    scenario.s_savings_rate = form.s_savings_rate.data

    scenario.ss_date = form.ss_date.data
    scenario.s_ss_date = form.s_ss_date.data

    scenario.ss_amount = form.ss_amount.data
    scenario.s_ss_amount = form.s_ss_amount.data

    scenario.retirement_age = form.retirement_age.data
    scenario.s_retirement_age = form.s_retirement_age.data

    scenario.ret_income = form.ret_income.data
    scenario.s_ret_income = form.s_ret_income.data

    scenario.ret_job_ret_age = form.ret_job_ret_age.data
    scenario.s_ret_job_ret_age = form.s_ret_job_ret_age.data

    scenario.lifespan_age = form.lifespan_age.data
    scenario.s_lifespan_age = form.s_lifespan_age.data

    scenario.windfall_amount = form.windfall_amount.data
    scenario.windfall_age = form.windfall_age.data

    scenario.has_spouse = form.has_spouse.data
    scenario.nestegg = form.nestegg.data
    scenario.drawdown = form.drawdown.data

    # Calculate ages from birthdates and save the,
    scenario.current_age = calculate_age(date.today(), form.birthdate.data)
    if (scenario.has_spouse):
        scenario.s_current_age = calculate_age(date.today(), form.s_birthdate.data)

    asset_mix_id, asset_mix = get_investment_from_select_field(form.investment)
    scenario.asset_mix_id = asset_mix_id
    return