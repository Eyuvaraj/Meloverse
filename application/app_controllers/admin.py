from flask import redirect, url_for, render_template, request, Flask, flash, Blueprint
from flask import current_app as app
from ..database import db
from ..models import Users
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from application.app_controllers import auth

admin=Blueprint('admin',__name__)

@admin.route("/admin/<user>", methods=["GET", "POST"])
@login_required
def admin_dashboard(user):
    return render_template("admin/admin_dashboard.html")