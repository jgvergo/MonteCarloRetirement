from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from Simulation import db
from Simulation.scenarios.forms import ScenarioForm, DisplaySimResultForm
from Simulation.models import Scenario
from flask_login import current_user, login_required
from Simulation.users.utils import calculate_age, calculate_full_ss_date

scenarios = Blueprint('scenarios', __name__)


@scenarios.route("/scenario/new", methods=['GET', 'POST'])
@login_required
def new_scenario():
    form = ScenarioForm()
    if form.validate_on_submit():
        scenario = Scenario()
        scenario.user_id = current_user.id

        scenario.title = form.title.data

        scenario.birthdate = form.birthdate.data
        scenario.s_birthdate = form.s_birthdate.data

        scenario.current_income = form.current_income.data
        scenario.s_current_income = form.s_current_income.data

        scenario.start_ss_date = form.start_ss_date.data
        scenario.s_start_ss_date = form.s_start_ss_date.data

        scenario.full_ss_amount = form.full_ss_amount.data
        scenario.s_full_ss_amount = form.s_full_ss_amount.data

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

        # Calculate age and full ss date from birthdate and save them
        if(scenario.has_spouse):
            scenario.s_full_ss_date = calculate_full_ss_date(scenario.s_birthdate)
            scenario.s_current_age = calculate_age(form.s_birthdate.data)

        scenario.current_age = calculate_age(form.birthdate.data)
        scenario.full_ss_date = calculate_full_ss_date(scenario.birthdate)

        db.session.add(scenario)
        db.session.commit()
        flash('Your scenario has been created!', 'success')
        return redirect(url_for('main.home'))
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
        scenario.title = form.title.data

        scenario.birthdate = form.birthdate.data
        scenario.s_birthdate = form.s_birthdate.data

        scenario.current_income = form.current_income.data
        scenario.s_current_income = form.s_current_income.data

        scenario.start_ss_date = form.start_ss_date.data
        scenario.s_start_ss_date = form.s_start_ss_date.data

        scenario.full_ss_amount = form.full_ss_amount.data
        scenario.s_full_ss_amount = form.s_full_ss_amount.data

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

        # Calculate age and full ss date from birthdate and save them
        scenario.full_ss_date = calculate_full_ss_date(scenario.birthdate)
        scenario.current_age = calculate_age(form.birthdate.data)

        if(scenario.has_spouse):
            scenario.s_full_ss_date = calculate_full_ss_date(scenario.s_birthdate)
            scenario.s_current_age = calculate_age(form.s_birthdate.data)

        db.session.commit()
        flash('Your scenario has been updated!', 'success')
        return redirect(url_for('scenarios.scenario', scenario_id=scenario.id))
    elif request.method == 'GET':
        form.title.data = scenario.title

        form.birthdate.data = scenario.birthdate
        form.s_birthdate.data = scenario.s_birthdate

        form.current_income.data = scenario.current_income
        form.s_current_income.data = scenario.s_current_income

        form.start_ss_date.data = scenario.start_ss_date
        form.s_start_ss_date.data = scenario.s_start_ss_date

        form.full_ss_amount.data = scenario.full_ss_amount
        form.s_full_ss_amount.data = scenario.s_full_ss_amount

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
    form.title.data = scenario.title
    form.image = '/static/profile_pics/eb8a48c7f4cf0cba.png'
    return render_template('display_sim_result.html', title='Simulated Scenario',
                               form=form, legend='Simulated Scenario', image_file=form.image)
