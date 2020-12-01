from flask import render_template, url_for, flash, redirect, request, Blueprint
from Simulation import db
from Simulation.asset_classes.forms import AssetClassForm, AssetClassListForm
from Simulation.models import AssetClass
from flask_login import login_required


asset_classes = Blueprint('asset_classes', __name__)


@asset_classes.route("/asset_classes/new", methods=['GET', 'POST'])
@login_required
def new_asset_class():
    form = AssetClassForm()
    if form.validate_on_submit():
        asset_class = AssetClass()
        if form.submit.data:
            # Pull the data from the form and save to database
            asset_class.title = form.title.data
            asset_class.avg_ret = form.avg_ret.data
            asset_class.std_dev = form.std_dev.data

            db.session.add(asset_class)
            db.session.commit()
            flash('Your asset class has been created!', 'success')
        else:
            flash('Changes to your asset class have been discarded', 'success')
        return redirect(url_for('asset_classes.list_asset_classes'))
    elif request.method == 'GET':
        return render_template('asset_class.html', form=form, legend='Create Asset Class')


@asset_classes.route("/asset_classes/<int:asset_class_id>/update", methods=['GET', 'POST'])
@login_required
def update_asset_class(asset_class_id):
    asset_class = AssetClass.query.get_or_404(asset_class_id)

    form = AssetClassForm()
    print("{:.2%}".format(asset_class.avg_ret))
    if form.validate_on_submit():
        if form.submit.data:
            # Pull the data from the form and save to database
            asset_class.title = form.title.data
            asset_class.avg_ret = form.avg_ret.data
            asset_class.std_dev = form.std_dev.data

            db.session.commit()
            flash('Your asset class data have been updated!', 'success')
        else:
            flash('Changes to your asset class have been discarded', 'success')
        return redirect(url_for('asset_classes.list_asset_classes'))
    elif request.method == 'GET':
        # Populate the form from the database
        form.title.data = asset_class.title
        form.std_dev.data = asset_class.std_dev
        form.avg_ret.data = asset_class.avg_ret
    return render_template('asset_class.html', form=form, legend='Update Asset Class')


@asset_classes.route("/asset_classes/list", methods=['GET', 'POST'])
@login_required
def list_asset_classes():
    page = request.args.get('page', 1, type=int)
    asset_class_list = AssetClass.query.order_by(AssetClass.date_created.desc()).paginate(page=page, per_page=7)
    form = AssetClassListForm()

    if form.validate_on_submit():
        if form.nas.data:
            return redirect(url_for('asset_classes.new_asset_class'))
        elif form.home.data:
            return redirect(url_for('main.home'))
    return render_template('asset_list.html', form=form, asset_classes=asset_class_list)
