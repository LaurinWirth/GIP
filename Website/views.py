from logging import error
import posixpath
from sys import meta_path
from flask import Blueprint, render_template, request, jsonify, abort
from flask.helpers import flash
from flask_login import login_required, current_user
from sqlalchemy.sql.functions import user
from werkzeug.utils import redirect
from . import db
from .models import User, Donation
import json
from dateutil import parser
from sqlalchemy import func, select, column, desc, text


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
        date_donated = parser.parse(request.form.get("donation-date"))

        new_donation = Donation(
            amount=amount,
            description=description,
            organisation=organisation,
            date_donated=date_donated,
            user_id=current_user.id,
        )
        db.session.add(new_donation)
        db.session.commit()

    total_donations = db.session.query(
        db.func.sum(Donation.amount).filter(Donation.user_id == current_user.id)
    ).scalar()
    donations_by_grp = (
        db.session.query(db.func.sum(Donation.amount), Donation.organisation)
        .filter(Donation.user_id == current_user.id)
        .group_by(Donation.organisation)
        .all()
    )

    return render_template(
        "Configure.html",
        user=current_user,
        total_donations=total_donations,
        donations_by_grp=donations_by_grp,
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

    # user = db.session.query(User).filter(User.id==id).all()

    user = User.query.get_or_404(id)
    total_donations = db.session.query(
        db.func.sum(Donation.amount).filter(Donation.user_id == id)
    ).scalar()
    donations_by_grp = (
        db.session.query(db.func.sum(Donation.amount), Donation.organisation)
        .filter(Donation.user_id == id)
        .group_by(Donation.organisation)
        .all()
    )
    dates = (
        db.session.query(db.func.sum(Donation.amount), Donation.date_donated)
        .filter(Donation.user_id == id)
        .group_by(Donation.date_donated)
        .order_by(Donation.date_donated)
        .all()
    )

    sum_donations = (
        db.session.query(
            User.first_name, Donation.user_id, func.sum(Donation.amount).label("Total")
        )
        .join(User, Donation.user_id == User.id)
        .group_by(Donation.user_id)
        .order_by(desc(text("Total")))
        .all()
    )

    groups_donations = []
    amount_by_grp = []

    for amount, groups in donations_by_grp:
        amount_by_grp.append(amount)
        groups_donations.append(groups)

    over_time_donations = []
    dates_labels = []
    cum_amount = 0

    for amount, date_donated in dates:
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
    )


@views.route("/dashboard/manage-plan")
@login_required
def manageplan():
    return render_template("managePlan.html", user=current_user)


@views.route("/dashboard/feedback")
@login_required
def feedback():
    return render_template("feedback.html", user=current_user)
