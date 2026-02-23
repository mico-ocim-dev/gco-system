"""Survey collection and analysis routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from utils.decorators import staff_required
from sqlalchemy import func

from extensions import db
from models import Survey, SurveyQuestion, SurveyResponse
from services.import_export import import_survey_responses_excel

surveys_bp = Blueprint("surveys", __name__)


@surveys_bp.route("/")
@login_required
@staff_required
def index():
    surveys = Survey.query.order_by(Survey.created_at.desc()).all()
    return render_template("surveys/index.html", surveys=surveys)


@surveys_bp.route("/create", methods=["GET", "POST"])
@login_required
@staff_required
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        desc = request.form.get("description", "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("surveys/form.html")
        s = Survey(title=title, description=desc or None)
        db.session.add(s)
        db.session.flush()
        # Questions
        types = request.form.getlist("question_type")
        for i, qtext in enumerate(request.form.getlist("question_text")):
            if (qtext or "").strip():
                qtype = types[i] if i < len(types) else "rating"
                q = SurveyQuestion(
                    survey_id=s.id,
                    question_text=qtext.strip(),
                    question_type=qtype,
                    order_index=i,
                )
                db.session.add(q)
        db.session.commit()
        flash("Survey created.", "success")
        return redirect(url_for("surveys.index"))
    return render_template("surveys/form.html")


@surveys_bp.route("/<int:sid>/respond", methods=["GET", "POST"])
def respond(sid):
    """Public survey response - no login required."""
    survey = Survey.query.get(sid)
    if not survey or not survey.is_active:
        flash("Survey not found or inactive.", "error")
        return redirect(url_for("surveys.index"))
    if request.method == "POST":
        for q in survey.questions:
            val = request.form.get(f"q{q.id}")
            if val is not None and val != "":
                try:
                    fval = float(val)
                    resp = SurveyResponse(survey_id=sid, question_id=q.id, response_value=fval)
                except ValueError:
                    resp = SurveyResponse(survey_id=sid, question_id=q.id, response_text=str(val))
                db.session.add(resp)
        db.session.commit()
        flash("Thank you for your response.", "success")
        return redirect(url_for("surveys.respond", sid=sid))
    return render_template("surveys/respond.html", survey=survey)


@surveys_bp.route("/<int:sid>")
@login_required
@staff_required
def detail(sid):
    survey = Survey.query.get(sid)
    if not survey:
        flash("Survey not found.", "error")
        return redirect(url_for("surveys.index"))
    # Compute averages per question
    avgs = (
        db.session.query(
            SurveyResponse.question_id,
            func.avg(SurveyResponse.response_value).label("avg"),
            func.count(SurveyResponse.id).label("count"),
        )
        .filter(SurveyResponse.survey_id == sid)
        .group_by(SurveyResponse.question_id)
        .all()
    )
    avg_map = {a[0]: {"avg": round(float(a[1] or 0), 2), "count": a[2]} for a in avgs}
    return render_template("surveys/detail.html", survey=survey, avg_map=avg_map)


@surveys_bp.route("/api/<int:sid>/chart-data")
@login_required
@staff_required
def api_chart_data(sid):
    """JSON for Chart.js - question averages."""
    avgs = (
        db.session.query(
            SurveyQuestion.question_text,
            func.avg(SurveyResponse.response_value).label("avg"),
        )
        .join(SurveyResponse, SurveyResponse.question_id == SurveyQuestion.id)
        .filter(SurveyQuestion.survey_id == sid)
        .group_by(SurveyQuestion.id)
        .all()
    )
    return jsonify({"labels": [a[0][:30] for a in avgs], "data": [round(float(a[1] or 0), 2) for a in avgs]})


@surveys_bp.route("/<int:sid>/import", methods=["GET", "POST"])
@login_required
@staff_required
def import_responses(sid):
    survey = Survey.query.get(sid)
    if not survey:
        flash("Survey not found.", "error")
        return redirect(url_for("surveys.index"))
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Please select a file.", "error")
            return redirect(url_for("surveys.import_responses", sid=sid))
        imp, failed, err = import_survey_responses_excel(file, sid, current_user.username)
        if err:
            flash(err, "error")
        else:
            flash(f"Imported {imp} responses. Failed: {failed}", "success" if failed == 0 else "warning")
        return redirect(url_for("surveys.detail", sid=sid))
    return render_template("surveys/import.html", survey=survey)
