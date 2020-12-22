from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from flask_login import current_user, login_required
from Simulation import db
from Simulation.scenarios.forms import ScenarioForm, DisplaySimResultForm
from Simulation.asset_classes.forms import populateInvestmentDropdown, getInvestmentDataFromSelectField, getAssetClass
from Simulation.models import Scenario
from Simulation.users.utils import calculate_age
from Simulation.MCSim import run_simulation
from Simulation.MCGraphs import plot_graphs
from Simulation.models import SimData
from datetime import date


scenarios = Blueprint('scenarios', __name__)


@scenarios.route("/scenario/new", methods=['GET', 'POST'])
@login_required
def new_scenario(titles=None):
    # User has clicked on "New Scenario" or has clicked "Save" after filling out a blank form or has clicked "Save and
    # Run" after filling out a blank form
    form = ScenarioForm()
    populateInvestmentDropdown(form.investment)

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

        populateInvestmentDropdown(form.investment, scenario.asset_class_id)

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

    form = DisplaySimResultForm()

    if form.validate_on_submit():
        form = ScenarioForm()
        form.id = scenario_id
        copyScenario2Form(scenario, form)
        return redirect(url_for('scenarios.update_scenario', scenario_id=scenario.id))
    else:
        # Do the simulation
        sd = SimData()
        p0, fd_output, dd_output, ss_output, sss_output, inv_output, inf_output, sd_output, cola_output = run_simulation(scenario, sd)

        plot_urls = plot_graphs(fd_output, dd_output, ss_output, sss_output,
                               inv_output, inf_output, sd_output, cola_output,
                               sd)

        form.title.data = scenario.title
        asset_class = getAssetClass(scenario.asset_class_id)
        nl = '\n'
        form.taf.data = 'Percent over zero: {:>.2f}%{}'\
                        'Primary user age: {}{}'\
                        "Spouse's age: {}{}"\
                        'Starting nestegg: {:,}{}'\
                        'Windfall amount: {:,}{}'\
                        'Windfall age: {}{}'\
                        'Social security amount(primary user): {:,}{}'\
                        'Social security date(primary user): {}{}'\
                        'Social security amount(spouse): {:,}{}'\
                        'Social security date(spouse): {}{}'\
                        'Asset class name: {}{}'\
                        'Asset class average return: {:.2f}%{}'\
                        'Asset class risk (std dev):{:.2f}%{}'\
                        'Number of Monte Carlo experiments: {:,}{}'\
                        'Inflation mean: {:.2f}%{}'\
                        'Inflation Standard Deviation:{:.2f}%{}'\
                        'Spend decay: {:.2f}%'.\
            format(p0, nl,
                   scenario.current_age, nl,
                   scenario.s_current_age, nl,
                   scenario.nestegg, nl,
                   scenario.windfall_amount, nl,
                   scenario.windfall_age, nl,
                   scenario.ss_amount, nl,
                   scenario.s_ss_date, nl,
                   scenario.s_ss_amount, nl,
                   scenario.s_ss_date, nl,
                   asset_class.title, nl,
                   100*asset_class.avg_ret, nl,
                   100*asset_class.std_dev, nl,
                   sd.num_exp, nl,
                   100*(sd.inflation[0]-1), nl,
                   100*sd.inflation[1], nl,
                   100*sd.spend_decay[0],50)


        return render_template('display_sim_result.html', title='Simulated Scenario',
                               form=form, legend='Simulated Scenario', plot_urls=plot_urls)

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

    asset_class_id, asset_class = getInvestmentDataFromSelectField(form.investment)
    scenario.asset_class_id = asset_class_id
    return