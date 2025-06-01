from flask import render_template, request, jsonify
from simulearn import app, db
from simulearn.utils import AuthController, LessonDesignerController, LearningRoomController
from flask_login import LoginManager, login_required, current_user
from simulearn.models import User, Lesson, ConversationHistory, UserCurrentLesson
from datetime import datetime

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@login_required
def home():
    lessons = Lesson.query.filter_by(created_by=current_user.id).all()
    current_lesson = UserCurrentLesson.query.filter_by(user_id=current_user.id).first()
    if current_lesson:
        sc_conversations = ConversationHistory.query \
                                            .filter_by(lesson_id=current_lesson.lesson_id, user_id=current_user.id, agent_role='sc') \
                                            .order_by(ConversationHistory.timestamp) \
                                            .all()
        tutor_conversations = ConversationHistory.query \
                                            .filter_by(lesson_id=current_lesson.lesson_id, user_id=current_user.id, agent_role='tutor') \
                                            .order_by(ConversationHistory.timestamp) \
                                            .all()
    else:
        sc_conversations = []
        tutor_conversations = []
    current_lesson_id = current_lesson.lesson_id if current_lesson else None

    return render_template("index.html", lessons = lessons,current_lesson_id = current_lesson_id, sc_conversations = sc_conversations, tutor_conversations = tutor_conversations)




auth_controller = AuthController()
app.add_url_rule("/register", view_func=auth_controller.register, methods=["GET","POST"])
app.add_url_rule("/login", view_func=auth_controller.login, methods=["GET","POST"])
app.add_url_rule("/logout", view_func=auth_controller.logout, methods=["GET"])
app.add_url_rule("/send_reset_password_link", view_func=auth_controller.send_reset_password_link, methods=["GET","POST"])
app.add_url_rule("/reset_password/<token>", view_func=auth_controller.reset_password, methods=["GET","POST"])

lesson_desinger_controller = LessonDesignerController()
app.add_url_rule("/save_lesson", view_func=login_required(lesson_desinger_controller.save_lesson), methods=["POST"])
app.add_url_rule("/design_lesson", view_func=login_required(lesson_desinger_controller.design_lesson), methods=["POST"])
app.add_url_rule("/load_lesson", view_func=login_required(lesson_desinger_controller.load_lesson), methods=["POST"])
app.add_url_rule("/delete_lesson", view_func=login_required(lesson_desinger_controller.delete_lesson), methods=["POST"])

learning_room_controller = LearningRoomController()
app.add_url_rule("/load_conversation", view_func=login_required(learning_room_controller.load_conversation), methods=["POST"])
app.add_url_rule("/chatbot/<agent_role>", view_func=login_required(learning_room_controller.chatbot), methods=["POST"])
app.add_url_rule("/clear_chat", view_func=login_required(learning_room_controller.clear_chat), methods=["POST"])