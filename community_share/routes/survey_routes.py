from flask import jsonify

from community_share.models.survey import Question, Answer
from community_share.routes import base_routes

def register_survey_routes(app):

    question_blueprint = base_routes.make_blueprint(Question, 'question')
    app.register_blueprint(question_blueprint)

    answer_blueprint = base_routes.make_blueprint(Answer, 'answer')
    app.register_blueprint(answer_blueprint)
