from logging import error
import posixpath
from sys import meta_path
from flask import Blueprint, render_template, request, jsonify, abort
from flask.helpers import flash
from flask_login import login_required, current_user
from sqlalchemy.sql.expression import false
from sqlalchemy.sql.functions import user
from werkzeug.utils import redirect
from . import db
from .models import User, Donation
import json
from dateutil import parser
from sqlalchemy import func, select, column, desc, text
import pandas as pd
from forex_python.converter import CurrencyRates

c = CurrencyRates()
eur = c.get_rate('EUR', 'USD')
pound = c.get_rate('EUR', 'USD')


views = Blueprint("views", __name__, template_folder="templates")


@views.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", user=current_user)


@views.route("/mission")
def mission():
    return render_template("vision.html")


@views.route("/subscribe")
def subscribe():
    return render_template("form.html")


@views.route("/dashboard/configure", methods=["GET", "POST"])
@login_required
def configureDashboard():
    if request.method == "POST":

        organisation = request.form.get("organisation-name")

        if request.form.get("donation-amount").isdigit():
            amount = request.form.get("donation-amount")
        else:
            flash("Please enter a valid digit", error)

        description = request.form.get("donation-description")
        currency = request.form.get("currency")
        date_donated = parser.parse(request.form.get("donation-date"))

        new_donation = Donation(
            amount=amount,
            currency = currency,
            description=description,
            organisation=organisation,
            date_donated=date_donated,
            user_id=current_user.id,
        )
        db.session.add(new_donation)
        db.session.commit()

    total_donations = (
        db.session.query(
        db.func.sum(Donation.amount), Donation.currency).filter(
            Donation.user_id == current_user.id).group_by(Donation.currency)
    ).all()



    donations_by_grp = (
        db.session.query(db.func.sum(Donation.amount), Donation.organisation, Donation.currency)
        .filter(Donation.user_id == current_user.id)
        .group_by(Donation.organisation, Donation.currency)
        .all()
    )

    return render_template(
        "Configure.html",
        user=current_user,
        total_donations=total_donations,
        donations_by_grp=donations_by_grp
    )


@views.route("/delete/<int:id>")
@login_required
def deleteDonation(id):

    donation_to_delete = Donation.query.get_or_404(id)
    if donation_to_delete:
        if donation_to_delete.user_id == current_user.id:
            try:
                db.session.delete(donation_to_delete)
                db.session.commit()
                return redirect("/dashboard/configure")

            except:
                return "There was a problem deleting that donation"

    return "There was a problem deleting that donation"


@views.route("/dashboard/public/<int:id>")
def publicdashboard(id):

    user = User.query.get_or_404(id)

    total_donations = (
    db.session.query(
    db.func.sum(Donation.amount), Donation.currency).filter(
        Donation.user_id == id).group_by(Donation.currency)
    ).all()

    donations_by_grp = (
    db.session.query(db.func.sum(Donation.amount), Donation.organisation, Donation.currency)
    .filter(Donation.user_id == id)
    .group_by(Donation.organisation, Donation.currency)
    .all()
    )
    
    dates = (
        db.session.query(db.func.sum(Donation.amount), Donation.date_donated, Donation.currency)
        .filter(Donation.user_id == id)
        .group_by(Donation.date_donated, Donation.currency)
        .order_by(Donation.date_donated)
        .all()
    )

    sum_donations = (
    db.session.query(
        User.first_name, Donation.user_id, 
        func.sum(
            Donation.amount), Donation.currency
    )
    .join(User, Donation.user_id == User.id)
    .group_by(Donation.user_id, User.first_name, Donation.currency)
    .order_by(desc(func.sum(Donation.amount)))
    .all()
)

    
 

    df = pd.DataFrame(sum_donations, columns= ['Name', 'Id', 'Amountin$', 'Currency'])
    
    def convert(c):

        if c['Currency'] == '€':
            return int(round(c['Amountin$'] * eur))
        elif c['Currency'] == '£':
            return int(round(c['Amountin$'] * pound))
        else:
            return int(round(c['Amountin$']))
        
        



    df['ConvertedAmount'] =df.apply(convert, axis=1)
    summaryTable = df.groupby(['Name', 'Id'])['ConvertedAmount'].sum().to_frame('SummedAmount').reset_index().sort_values(by='SummedAmount', ascending=False)
    
    print(summaryTable)

    groups_donations = []
    amount_by_grp = []
    lifetime_donations = 0

    for amount, groups, currency in donations_by_grp:
        if currency == '€':
            amount = amount * c.get_rate('EUR', 'USD')
        elif currency == '£':
            amount = amount* c.get_rate('GBP', 'USD')
        amount_by_grp.append(amount)
        groups_donations.append(groups)
        lifetime_donations = lifetime_donations + amount

    over_time_donations = []
    dates_labels = []
    cum_amount = 0

    for amount, date_donated, currency in dates:
        if currency == '€':
            amount = amount * c.get_rate('EUR', 'USD')
        elif currency == '£':
            amount = amount* c.get_rate('GBP', 'USD')
        cum_amount = cum_amount + amount
        over_time_donations.append(cum_amount)
        dates_labels.append(date_donated.strftime("%Y-%m-%d"))
        

    return render_template(
        "publicdashboard.html",
        user=user,
        total_donations=total_donations,
        donations_by_grp=donations_by_grp,
        over_time_donations=json.dumps(over_time_donations),
        dates_labels=json.dumps(dates_labels),
        groups_donations=json.dumps(groups_donations),
        amount_by_grp=json.dumps(amount_by_grp),
        sum_donations=sum_donations,
        lifetime_donations = lifetime_donations,
        eur = eur, pound = pound,
        summaryTable = summaryTable
    )


@views.route("/dashboard/manage-plan")
@login_required
def manageplan():
    return render_template("managePlan.html", user=current_user)


@views.route("/dashboard/feedback")
@login_required
def feedback():
    return render_template("feedback.html", user=current_user)
