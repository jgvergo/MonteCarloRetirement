from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from Simulation import db
from Simulation.userdata.forms import UserDataForm
from Simulation.models import UserData, User
from flask_login import current_user, login_required
from Simulation.users.utils import calculate_age, calculate_full_ss_date
from datetime import date

userdata = Blueprint('userdata', __name__)


@userdata.route("/userdata/update", methods=['GET', 'POST'])
@login_required
def update_userdata():
    user = User.query.get_or_404(current_user.id)

    # If we have not created a userdata object, create it here
    if user.userdata is None:
        user.userdata = UserData()
        user.userdata.id = current_user.id
    userdata = user.userdata

    # This should never fail, but just in case...
    if userdata.id != current_user.id:
        abort(403)

    form = UserDataForm()

    if form.validate_on_submit():
        if(form.submit.data):
            # Pull the data from the form and save to database
            userdata.title = form.title.data
            userdata.birthdate = form.birthdate.data
            userdata.current_income = form.current_income.data
            userdata.lifespan_age = form.lifespan_age.data
            userdata.full_ss_amount = form.full_ss_amount.data
            userdata.nestegg = form.nestegg.data
            userdata.drawdown = form.drawdown.data
            userdata.has_spouse = form.has_spouse.data
            userdata.s_birthdate = form.s_birthdate.data
            userdata.s_current_income = form.s_current_income.data
            userdata.s_lifespan_age = form.s_lifespan_age.data
            userdata.s_full_ss_amount = form.s_full_ss_amount.data

            # Calculate age and full ss date from birthdate and save them
            userdata.full_ss_date = calculate_full_ss_date(userdata.birthdate)
            userdata.s_full_ss_date = calculate_full_ss_date(userdata.s_birthdate)
            userdata.current_age = calculate_age(date.today(), form.birthdate.data)
            userdata.s_current_age = calculate_age(date.today(), form.s_birthdate.data)

            db.session.commit()
            flash('Your user data have been updated!', 'success')
        else:
            flash('Changes to your user data have been discarded', 'success')
        return redirect(url_for('main.home'))
    elif request.method == 'GET':
        #Populate the form from the database
        form.birthdate.data = userdata.birthdate
        form.current_income.data = userdata.current_income
        form.lifespan_age.data = userdata.lifespan_age
        form.full_ss_amount.data = userdata.full_ss_amount
        form.nestegg.data = userdata.nestegg
        form.drawdown.data = userdata.drawdown
        form.has_spouse.data = userdata.has_spouse
        form.s_birthdate.data = userdata.s_birthdate
        form.s_current_income.data = userdata.s_current_income
        form.s_lifespan_age.data = userdata.s_lifespan_age
        form.s_full_ss_amount.data = userdata.s_full_ss_amount
    return render_template('userdata.html', form=form, legend='Update User Data')