from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import desc
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.admin import admin_blueprint
from application.admin.forms import AddUserForm
from application.auth.models import User, TypeOfUser, CAPABILITIES, MANAGE_SYSTEM, MANAGE_USERS
from application.cms.models import user_measure
from application.cms.page_service import page_service
from application.utils import create_and_send_activation_email, user_can
from application.cms.utils import get_form_errors


@admin_blueprint.route("")
@login_required
@user_can(MANAGE_USERS)
def index():
    return render_template("admin/index.html")


@admin_blueprint.route("/users")
@login_required
@user_can(MANAGE_USERS)
def users():
    return render_template(
        "admin/users.html", users=User.query.order_by(User.user_type, desc(User.active), User.email).all()
    )


@admin_blueprint.route("/users/<int:user_id>")
@login_required
@user_can(MANAGE_USERS)
def user_by_id(user_id):
    user = User.query.filter_by(id=user_id).one()
    if user.user_type == TypeOfUser.DEPT_USER:
        latest_measure_versions = page_service.get_latest_version_of_all_measures(include_not_published=True)
        shared = user.measures
    else:
        latest_measure_versions = []
        shared = []

    return render_template("admin/user.html", user=user, latest_measure_versions=latest_measure_versions, shared=shared)


@admin_blueprint.route("/users/<int:user_id>/share", methods=["POST"])
@login_required
@user_can(MANAGE_USERS)
def share_page_with_user(user_id):
    measure_id = request.form.get("measure-picker")
    measure = page_service.get_measure_from_measure_version_id(measure_id)
    user = User.query.get(user_id)
    if not user.is_departmental_user():
        flash("User %s is not a departmental user" % user.email, "error")
    if user in measure.shared_with:
        flash("User %s already has access to %s " % (user.email, measure.latest_version.title), "error")
    else:
        measure.shared_with.append(user)
        db.session.commit()
    return redirect(url_for("admin.user_by_id", user_id=user_id, _anchor="departmental-sharing"))


@admin_blueprint.route("/users/<int:user_id>/remove-share/<measure_id>")
@login_required
@user_can(MANAGE_USERS)
def remove_shared_page_from_user(user_id, measure_id):
    db.session.execute(
        user_measure.delete().where(user_measure.c.user_id == user_id).where(user_measure.c.measure_id == measure_id)
    )
    db.session.commit()
    return redirect(url_for("admin.user_by_id", user_id=user_id, _anchor="departmental-sharing"))


@admin_blueprint.route("/users/add", methods=("GET", "POST"))
@login_required
@user_can(MANAGE_USERS)
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():

        existing_user = User.query.filter(User.email.ilike(form.email.data)).first()
        if existing_user:
            message = "User: %s is already in the system" % existing_user.email
            flash(message, "error")
            return redirect(url_for("admin.users"))

        user = User(email=form.email.data)
        if form.user_type.data == TypeOfUser.DEPT_USER.name:
            user.user_type = TypeOfUser.DEPT_USER
            user.capabilities = CAPABILITIES[TypeOfUser.DEPT_USER]
        elif form.user_type.data == TypeOfUser.RDU_USER.name:
            user.user_type = TypeOfUser.RDU_USER
            user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
        elif form.user_type.data == TypeOfUser.DEV_USER.name:
            user.user_type = TypeOfUser.DEV_USER
            user.capabilities = CAPABILITIES[TypeOfUser.DEV_USER]
        else:
            flash("Only RDU or DEPT users can be created using this page")
            abort(401)

        db.session.add(user)
        db.session.commit()
        create_and_send_activation_email(form.email.data, current_app)
        return redirect(url_for("admin.users"))

    return render_template("admin/add_user.html", form=form, errors=get_form_errors(forms=[form]))


@admin_blueprint.route("/users/<int:user_id>/resend-account-activation-email")
@login_required
@user_can(MANAGE_USERS)
def resend_account_activation_email(user_id):
    try:
        user = User.query.get(user_id)
        create_and_send_activation_email(user.email, current_app)
        return redirect(url_for("admin.users"))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(400)


@admin_blueprint.route("/users/<int:user_id>/deactivate")
@login_required
@user_can(MANAGE_USERS)
def deactivate_user(user_id):
    try:
        user = User.query.get(user_id)
        user.active = False
        db.session.commit()
        flash("User account for: %s deactivated" % user.email)
        return redirect(url_for("admin.users"))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(404)
    return render_template("admin/users.html", users=users)


@admin_blueprint.route("/users/<int:user_id>/delete")
@login_required
@user_can(MANAGE_USERS)
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        for measure in user.measures:
            db.session.execute(
                user_measure.delete()
                .where(user_measure.c.user_id == user.id)
                .where(user_measure.c.measure_id == measure.id)
            )
            db.session.commit()
        db.session.delete(user)
        db.session.commit()
        flash("User account for: %s deleted" % user.email)
        return redirect(url_for("admin.users"))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(404)
    return render_template("admin/users.html", users=users)


@admin_blueprint.route("/users/<int:user_id>/make-admin")
@login_required
@user_can(MANAGE_USERS)
def make_admin_user(user_id):
    try:
        user = User.query.get(user_id)
        if user.is_rdu_user():
            user.user_type = TypeOfUser.ADMIN_USER
            user.capabilities = CAPABILITIES[TypeOfUser.ADMIN_USER]
            db.session.commit()
            flash("User %s is now an admin user" % user.email)
        else:
            flash("Only RDU users can be made admin")
        return redirect(url_for("admin.user_by_id", user_id=user.id))
    except NoResultFound as e:
        current_app.logger.error(e)
        abort(404)


@admin_blueprint.route("/users/<int:user_id>/make-rdu-user")
@login_required
@user_can(MANAGE_USERS)
def make_rdu_user(user_id):
    user = User.query.get(user_id)
    if user.id == current_user.id:
        flash("You can't remove your own admin rights")
    elif user.user_type == TypeOfUser.ADMIN_USER:
        user.user_type = TypeOfUser.RDU_USER
        user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
        db.session.commit()
        flash("User %s is now a standard RDU user" % user.email)
    else:
        flash("Only admins can be changed to standard RDU user")
    return redirect(url_for("admin.user_by_id", user_id=user.id))


@admin_blueprint.route("/site-build")
@login_required
@user_can(MANAGE_SYSTEM)
def site_build():
    return render_template("admin/site_build.html")
