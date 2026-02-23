"""Survey and response models."""
from datetime import datetime
from extensions import db


class Survey(db.Model):
    """Survey definitions."""

    __tablename__ = "surveys"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    questions = db.relationship("SurveyQuestion", backref="survey", lazy="dynamic", cascade="all, delete-orphan")
    responses = db.relationship("SurveyResponse", backref="survey", lazy="dynamic", cascade="all, delete-orphan")


class SurveyQuestion(db.Model):
    """Questions within a survey."""

    __tablename__ = "survey_questions"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default="rating")  # rating, text, choice
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    responses = db.relationship("SurveyResponse", backref="question", lazy="dynamic", foreign_keys="SurveyResponse.question_id")


class SurveyResponse(db.Model):
    """Individual survey responses."""

    __tablename__ = "survey_responses"

    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("surveys.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("survey_questions.id"), nullable=False)
    response_value = db.Column(db.Float, nullable=True)  # For numeric/rating
    response_text = db.Column(db.Text, nullable=True)  # For text responses
    respondent_id = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
