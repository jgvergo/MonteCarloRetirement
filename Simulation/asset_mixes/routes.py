from flask import render_template, url_for, flash, redirect, request, Blueprint
from Simulation import db
from Simulation.asset_mixes.forms import AssetMixForm, AssetMixListForm
from Simulation.models import AssetMix, AssetMixAssetClass
from flask_login import login_required
from Simulation.utils import populate_investment_dropdown
from wtforms import SelectField, DecimalField, SubmitField
from wtforms.validators import InputRequired
from Simulation.utils import get_key, does_key_exist

asset_mixes = Blueprint('asset_mixes', __name__)


@asset_mixes.route("/asset_mixes/new", methods=['GET', 'POST'])
@login_required
def new_asset_mix():
    form = AssetMixForm(request.form)
    # The method is "GET" if the user clicks the "New Asset Mix" button
    if request.method == 'GET':
        # Create a blank AssetMix
        asset_mix = AssetMix()
        asset_mix.title = ''
        asset_mix.description = ''
        db.session.add(asset_mix)
        db.session.commit()

        # Create a blank AssetMixAssetClass
        amac = AssetMixAssetClass()
        amac.asset_mix_id = asset_mix.id
        amac.asset_class_id = 1
        amac.percentage = 0.0
        db.session.add(amac)
        db.session.commit()
        BuildACAM([amac], form)

        # redirect to the update URL (seemed easiest way to handle it)
        return redirect('{:,.0f}/update'.format(asset_mix.id))
    print('HELP - asset_mixes/routes.py')  # We should never get here
    return


# Wipes the existing AssetClassAssetMixes from the database, scrapes the UI for the current state
# and saves it back to the database. If the user is attempting to Save the ACAM, then check to make
# sure the percentages add up to 100. Otherwise, allow them to add up to something other than 100
def save_ui_state(request, form, asset_mix_id, check_pcts):
    acs = request.form.getlist('Asset Class')
    pcts = request.form.getlist('percentage')

    # If indicated, check to make sure the percentages add up to 100
    if check_pcts:
        total = 0
        for item in pcts:
            total += float(item)
        if total != 100:
            return "Not100"

    # Delete the old AssetMixAssetClasses from the database
    AssetMixAssetClass.query.filter_by(asset_mix_id=int(asset_mix_id)).delete()

    # Save the new information
    for idx, ac in enumerate(acs):
        acam = AssetMixAssetClass()
        acam.asset_class_id = int(acs[idx])
        acam.asset_mix_id = int(asset_mix_id)
        acam.percentage = float(pcts[idx])
        db.session.add(acam)
        db.session.commit()
    asset_mix = AssetMix.query.get_or_404(asset_mix_id)
    asset_mix.title = form.title.data
    db.session.commit()

    return

@asset_mixes.route("/asset_mixes/<int:asset_mix_id>/update", methods=['GET', 'POST'])
@login_required
def update_asset_mix(asset_mix_id):
    # There are 5 circumstances that get us here: 1) The user has clicked on "New Asset Mix", 2) User is
    # removing an asset class, 3) User is adding an asset class and 4) User is saving the AssetMix 5) The User
    # is deleting the AssetMix

    # Get info from form and request
    form = AssetMixForm(request.form)
    req_dict = request.form.to_dict()

    acs = request.form.getlist('Asset Class')
    pcts = request.form.getlist('percentage')
    # If it is a POST request, check to see if the user wants to 1) remove an Asset Class, 2) add an Asset Class
    if request.method == "POST":

        # Look for a key that has a value of 'x', in which case the user clicked on an x to remove an Asset Class
        remove_key = get_key(req_dict, 'x')
        if remove_key != 'NoKey':
            # Remove the AssetMixAssetClass
            AssetMixAssetClass.query.filter_by(id=int(remove_key)).delete()
            db.session.commit()

            # Rebuild the form and re-render it
            asset_mix_asset_classes = AssetMixAssetClass.query.filter_by(asset_mix_id=asset_mix_id).all()
            BuildACAM(asset_mix_asset_classes, form)
            return render_template('asset_mix.html', form=form, legend='Update Asset Mix',asset_mix_id=asset_mix_id)

        # If a key by the name of 'add' exists, the user is trying to add a new Asset Class
        if does_key_exist(req_dict, 'add'):
            # First, save the current information from the form in case the user has made changes
            save_ui_state(request, form=form, asset_mix_id=asset_mix_id, check_pcts=False)

            # Build a new record and add it to the database
            asset_mix_asset_class = AssetMixAssetClass()
            asset_mix_asset_class.asset_mix_id = asset_mix_id
            asset_mix_asset_class.asset_class_id = 1
            asset_mix_asset_class.percentage = 0
            db.session.add(asset_mix_asset_class)
            db.session.commit()

            # Rebuild the form and re-render it
            asset_mix_asset_classes = AssetMixAssetClass.query.filter_by(asset_mix_id=asset_mix_id).all()
            BuildACAM(asset_mix_asset_classes, form)
            return render_template('asset_mix.html', form=form, legend='Update Asset Mix', asset_mix_id=asset_mix_id)

    asset_mix = AssetMix.query.get_or_404(asset_mix_id)

    # This section handles the Save and Delete buttons
    if form.validate_on_submit():
        if form.submit.data:
            # Save was clicked, make sure the Asset Classes have been selected and the percentages add up to zero
            if save_ui_state(request, form=form, asset_mix_id=asset_mix_id, check_pcts=True) == 'Not100':
                # Rebuild the form so the user can continue editing it
                asset_mix_asset_classes = AssetMixAssetClass.query.filter_by(asset_mix_id=asset_mix_id).all()
                for idx, acam in enumerate(asset_mix_asset_classes):
                    acam.percentage = float(pcts[idx])
                    acam.asset_class_id = int(acs[idx])
                BuildACAM(asset_mix_asset_classes, form)
                flash('Percentages must add up to 100', 'danger')
                return render_template('asset_mix.html', form=form, legend='Update Asset Mix',
                                       asset_mix_id=asset_mix_id)
            else:
                return redirect(url_for('asset_mixes.list_asset_mixes'))

            # Delete the old AssetMixAssetClasses from the database
            AssetMixAssetClass.query.filter_by(asset_mix_id=int(asset_mix_id)).delete()

            # Save the new information
            for idx, ac in enumerate(acs):
                acam = AssetMixAssetClass()
                acam.asset_class_id = int(acs[idx])
                acam.asset_mix_id = int(asset_mix_id)
                acam.percentage = float(pcts[idx])
                db.session.add(acam)
                db.session.commit()

            asset_mix.title = form.title.data
            db.session.commit()
            flash('Your asset mix data have been updated!', 'success')
        elif form.delete.data:
            # Delete the old AssetMixAssetClasses and the AssetMix
            AssetMixAssetClass.query.filter_by(asset_mix_id=int(asset_mix_id)).delete()
            AssetMix.query.filter_by(id=int(asset_mix_id)).delete()
            db.session.commit()
            flash('Your asset mix was deleted!', 'success')

        return redirect(url_for('asset_mixes.list_asset_mixes'))

    elif request.method == 'GET':
        # Populate the form from the database
        form.title.data = asset_mix.title
        asset_mix_asset_classes = AssetMixAssetClass.query.filter_by(asset_mix_id=asset_mix.id).all()
        BuildACAM(asset_mix_asset_classes, form)
    return render_template('asset_mix.html', form=form, legend='Update Asset Mix')


# Given a set of AssetClassAssetMixes, dynamically populate the form
def BuildACAM(asset_mix_asset_classes, form):
    form.investments = []
    foo = 0
    for row in asset_mix_asset_classes:
        bletch = SubmitField(label='x')
        remove = bletch.bind(form=form, name=str(row.id))

        bletch = SelectField(label='Asset Class', coerce=int, validate_choice=False)
        sf = bletch.bind(form=form, name='Asset Class')
        populate_investment_dropdown(sf, row.asset_class_id, kind='AssetClass')

        bletch = DecimalField(places=3, number_format="{:.2%}", validators=[InputRequired(message='Required')])
        pct = bletch.bind(form=form, name='percentage')
        pct.data = row.percentage

        form.investments.append([sf, pct, remove])
        foo += 1
    return

@asset_mixes.route("/asset_mixes/list", methods=['GET', 'POST'])
@login_required
def list_asset_mixes():
    page = request.args.get('page', 1, type=int)
    asset_mix_list = AssetMix.query.order_by(AssetMix.title.asc()).paginate(page=page, per_page=10)
    form = AssetMixListForm()

    if form.validate_on_submit():
        if form.nam.data:
            return redirect(url_for('asset_mixes.new_asset_mix'))
        elif form.home.data:
            return redirect(url_for('main.home'))
    return render_template('asset_mix_list.html', form=form, asset_mixes=asset_mix_list)
