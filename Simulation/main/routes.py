from flask import Blueprint, render_template, request
from flask_login import current_user, login_manager
from Simulation.models import Scenario


main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    user_id = current_user.get_id()
    page = request.args.get('page', 1, type=int)
    scenarios = Scenario.query.filter_by(user_id=user_id)\
                        .order_by(Scenario.date_posted.desc())\
                        .paginate(page=page, per_page=10)
    return render_template('home.html', scenarios=scenarios)


@main.route("/about")
def about():
    return render_template('about.html', title='About')


@main.route("/disclaimer")
def disclaimer():
    return render_template('disclaimer.html', title='Disclaimer')


@main.route("/privacy-policy")
def privacy_policy():
    return render_template('privacy-policy.html', title='Privacy Policy')

@main.route("/FAQ")
def FAQ():
    return render_template('FAQ.html', title='Frequently Asked Questions')