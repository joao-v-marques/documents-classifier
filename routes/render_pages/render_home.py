from flask import Blueprint, render_template

bp_render_home = Blueprint("bp_render_home", __name__)

@bp_render_home.route("/")
def render_home():
    return render_template("home.html")