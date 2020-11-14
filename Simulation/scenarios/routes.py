from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from Simulation import db
from Simulation.scenarios.forms import ScenarioForm, DisplaySimResultForm
from Simulation.models import Scenario
from flask_login import current_user, login_required


scenarios = Blueprint('scenarios', __name__)


@scenarios.route("/scenario/new", methods=['GET', 'POST'])
@login_required
def new_scenario():
    form = ScenarioForm()
    if form.validate_on_submit():
        scenario = Scenario(title=form.title.data, total_amount=form.total_amount.data,
                            asset_class=form.asset_class.data, author=current_user)
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
        scenario.total_amount = form.total_amount.data
        scenario.asset_class = form.asset_class.data
        db.session.commit()
        flash('Your scenario has been updated!', 'success')
        return redirect(url_for('scenarios.scenario', scenario_id=scenario.id))
    elif request.method == 'GET':
        form.title.data = scenario.title
        form.total_amount.data = scenario.total_amount
        form.asset_class.data = scenario.asset_class
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
