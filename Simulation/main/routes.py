from flask import Blueprint, render_template, request
from Simulation.models import Scenario


main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    scenarios = Scenario.query.order_by(Scenario.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('home.html', scenarios=scenarios)


@main.route("/about")
def about():
    return render_template('about.html', title='About')