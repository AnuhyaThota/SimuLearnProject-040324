#import all the necessary libraries
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_user, logout_user
from simulearn import db, mail
from config import Config
from simulearn.models import User, Lesson, ConversationHistory, UserCurrentLesson
from flask_mail import Message
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()



client = OpenAI(api_key=os.getenv("GOOGLE_API_KEY"),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def get_chat_response(messages):
    try:
        # Ensure the model name "gemini-2.0-flash" is correct for your custom base_url.
        # For standard Google Gemini API, model names are typically like "gemini-pro" or "gemini-1.5-flash-latest".
        response = client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=messages,
            temperature=1
        )
        return response.choices[0].message.content
    except Exception as e:
        # Log the error for debugging purposes in a real application
        # from flask import current_app
        # current_app.logger.error(f"AI chat completion failed: {e}", exc_info=True)
        print(f"Error in get_chat_response: {e}") # Simple print for development
        return "I'm sorry, but I encountered an issue while trying to generate a response. Please try again later."

    
class AuthController:
    def register(self):
        if current_user.is_authenticated:
            return redirect(url_for("home"))
    
        form_data = {}
        if request.method == 'POST':
            fullname = request.form.get("fullname")
            username = request.form.get("username")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            email = request.form.get("email")
        
            form_data = {
                'fullname': fullname,
                'username': username,
                'email': email
            } # Store data for re-rendering, not passwords

            if User.query.filter_by(username=username).first():
                flash("Username already exists!", "danger")
                return render_template("register.html", **form_data)

            if User.query.filter_by(email=email).first():
                flash("Email already exists!", "danger")
                return render_template("register.html", **form_data)

            if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return render_template("register.html", **form_data)
            
            # Optional: Add password strength validation here
            # if len(password) < 8:
            #     flash("Password must be at least 8 characters long.", "danger")
            #     return render_template("register.html", **form_data)
            
            new_user = User(fullname=fullname, email=email, username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
    
        return render_template("register.html", **form_data)
    
    def login(self):
        if current_user.is_authenticated:
            return redirect(url_for("home"))
    
        if request.method == 'POST':
            username = request.form.get("username")
            password = request.form.get("password")
            user = User.query.filter_by(username=username).first() #.one_or_none()

            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("home"))
            else: # Handles both user not found or password incorrect
                flash("Please check your login details and try again.", "danger")
                return render_template("login.html", username=username) # Pass username back
    
        return render_template("login.html", username=request.form.get("username", ""))
    
    def logout(self):
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))
            
    def send_reset_password_link(self):
        if current_user.is_authenticated:
            return redirect(url_for('home'))

        if request.method == 'POST':
            email = request.form.get("email")
            user = User.query.filter_by(email=email).first()
            
            if user:
                token = user.get_reset_token()
                # Ensure MAIL_USERNAME is set in your Config or use app.config['MAIL_DEFAULT_SENDER']
                sender_email = Config.MAIL_USERNAME if hasattr(Config, 'MAIL_USERNAME') else 'noreply@example.com'
                msg = Message("Password Reset Request", 
                              sender=sender_email, 
                              recipients=[user.email])
                msg.body = f'''To reset your password, visit the following link:
{url_for("reset_password", token=token, _external=True)}
This link will expire in 30 minutes.
If you did not make this request then simply ignore this email and no changes will be made.
'''
                mail.send(msg)
                flash("An email has been sent with instructions to reset your password.", "info")
                return redirect(url_for("login"))
            

        return render_template("send_reset_password_link.html", email=request.form.get("email", ""))
    
    def reset_password(self, token):
        if current_user.is_authenticated:
            return redirect(url_for('home'))
            
        user=User.verify_reset_token(token)
        if not user:
            flash("That is an invalid or expired token. Please try requesting a new password reset link.", "warning")
            return redirect(url_for("send_reset_password_link"))
        
        if request.method == 'POST':
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return render_template("reset_password.html", token=token)
            
            # Optional: Add password strength validation here
            # if len(password) < 8:
            #     flash("Password must be at least 8 characters long.", "danger")
            #     return render_template("reset_password.html", token=token)

            user.set_password(password)
            db.session.commit()
            flash("Your password has been updated! You are now able to log in.", "success")
            return redirect(url_for("login"))
        return render_template("reset_password.html", token=token)

class LessonDesignerController:

    @staticmethod
    def prepare_lesson_attributes(userPrompt):
        system_message = f"""
        You are a helpful assistant. Leaner is trying to design his lesson. Lesson designer is a tool that helps learner to create a lesson. It has following attributes:
        - lesson title : this is the title of the lesson
        - lesson description : this is the description of the lesson, it provides a brief overview and objectives of the lesson
        - Tutor description : Tutor is a role-play character that helps learner to understand the lesson, guides the learner to achieve the learning objectives and provides feedback
        - Simu description : Simu is a role-play character that plays a complementary role based on the context of the lesson. It creates an experience scenario for the learner to understand the lesson better.
        As a helpful assistant, you answer the learners queries and help to fill in the information of the about attributes. Your answer should be concise and to the point.
        Following is the user prompt that learner has provided about what they want to learn:

        {userPrompt}
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": "What should be the title of the lesson?"}
        ]
        lesson_title = get_chat_response(messages)
        messages.append({"role": "assistant", "content": lesson_title})
        messages.append({"role": "user", "content": "What should be the description of the lesson?"})
        lesson_desc = get_chat_response(messages)
        messages.append({"role": "assistant", "content": lesson_desc})
        messages.append({"role": "user", "content": "What should be the tutor description?"})
        tutor_prompt = get_chat_response(messages)
        messages.append({"role": "assistant", "content": tutor_prompt})
        messages.append({"role": "user", "content": "What should be the simu description?"})
        sc_prompt = get_chat_response(messages)

        return lesson_title, lesson_desc, tutor_prompt, sc_prompt

    def get_lesson_list(self):
        lessons = Lesson.query.filter_by(created_by=current_user.id).all()
        # Sort by id or another field if preferred, e.g., lesson_title
        lesson_list = [{"lessonID": lesson.id, "lessonTitle": lesson.lesson_title} for lesson in sorted(lessons, key=lambda x: x.id, reverse=True)]
        return lesson_list
    
    def save_lesson(self):
        userPrompt = request.get_json().get("userPrompt")
        lessonTitle = request.get_json().get("lessonTitle")
        lessonDesc = request.get_json().get("lessonDesc")
        tutorPrompt = request.get_json().get("tutorPrompt")
        scPrompt = request.get_json().get("scPrompt")
        lesson = Lesson(created_by=current_user.id, 
                        user_prompt=userPrompt, 
                        lesson_title=lessonTitle, 
                        lesson_desc=lessonDesc, 
                        tutor_prompt=tutorPrompt, 
                        sc_prompt=scPrompt)
        db.session.add(lesson)
        db.session.commit()
        updated_lesson_list = self.get_lesson_list() # Fetch fresh list

        return jsonify({
            "lessonID": lesson.id,
            "lessonTitle": lesson.lesson_title,
            "lessonList": updated_lesson_list
        })
    
    def design_lesson(self):
        userPrompt = request.get_json().get("userPrompt")
        lesson_title, lesson_desc, tutor_prompt, sc_prompt = LessonDesignerController.prepare_lesson_attributes(userPrompt)
        return jsonify({"userPrompt": userPrompt,
                            "lessonTitle": lesson_title,
                            "lessonDesc": lesson_desc,
                            "tutorPrompt": tutor_prompt,
                            "scPrompt": sc_prompt})
    
    def load_lesson(self):
        lessonID = request.get_json().get("lessonID")
        # Ensure the lesson belongs to the current user
        lesson = Lesson.query.filter_by(id=lessonID, created_by=current_user.id).first()
        if not lesson:
            return jsonify({"error": "Lesson not found or not authorized"}), 404
            
        return jsonify({
            "lessonID": lesson.id,
            "lessonTitle": lesson.lesson_title,
            "lessonDesc": lesson.lesson_desc,
            "userPrompt": lesson.user_prompt,
            "tutorPrompt": lesson.tutor_prompt,
            "scPrompt": lesson.sc_prompt,
        })
    def delete_lesson(self):
        lessonID = request.get_json().get("lessonID")
        # Ensure the lesson belongs to the current user before deleting
        lesson = Lesson.query.filter_by(id=lessonID, created_by=current_user.id).first()
        if not lesson:
            return jsonify({"error": "Lesson not found or not authorized to delete"}), 404

        # Delete related UserCurrentLesson entries first
        UserCurrentLesson.query.filter_by(lesson_id=lessonID, user_id=current_user.id).delete()
        # Then delete conversation history for the current user and this lesson
        db.session.delete(lesson)
        ConversationHistory.query.filter_by(lesson_id=lessonID, user_id=current_user.id).delete()
        db.session.commit()
        updated_lesson_list = self.get_lesson_list()
        return jsonify({
            "lessonList": updated_lesson_list,
            "message": "Lesson deleted successfully."
        })

class LearningRoomController:
    # No __init__ or instance variables for conversation history needed here
    # Controller should be stateless regarding user conversation data.

    def load_conversation(self):
        lessonID = request.get_json().get("lessonID")

        # Ensure the lesson exists and belongs to the current user
        lesson = Lesson.query.filter_by(id=lessonID, created_by=current_user.id).first()
        if not lesson:
            return jsonify({"error": "Lesson not found or you are not authorized to load it."}), 404

        user_current_lesson = UserCurrentLesson.query.filter_by(user_id=current_user.id).first()
        if user_current_lesson:
            user_current_lesson.lesson_id = lessonID
        else:
            user_current_lesson = UserCurrentLesson(user_id=current_user.id, lesson_id=lessonID)
            db.session.add(user_current_lesson)
        db.session.commit()

        db_conversations = ConversationHistory.query.filter_by(
            lesson_id=lessonID, 
            user_id=current_user.id
        ).order_by(ConversationHistory.timestamp).all()

        formatted_conversations = [
            {"user_input": conv.user_input, "response": conv.response, "agent_role": conv.agent_role, "timestamp": conv.timestamp.isoformat()}
            for conv in db_conversations
        ]
        return jsonify({"conversations": formatted_conversations, "lessonTitle": lesson.lesson_title})
    
    def chatbot(self, agent_role):
        user_input = request.get_json().get("userText")
        lessonID = request.get_json().get("lessonID")

        # Ensure the lesson exists and belongs to the current user
        lesson = Lesson.query.filter_by(id=lessonID, created_by=current_user.id).first()
        if not lesson:
            return jsonify({"error": "Lesson not found or not authorized."}), 404

        # Fetch all conversation history for this lesson and user to build context
        all_conversations_db = ConversationHistory.query.filter_by(
            lesson_id=lessonID,
            user_id=current_user.id
        ).order_by(ConversationHistory.timestamp).all()

        messages_for_llm = []
        chatbot_output = "No response generated." # Default

        if agent_role == "tutor":
            tutor_system_prompt_base = f"""
You are a tutor. Your role is to help the learner to understand the lesson, guide the learner to achieve the learning objectives and provide feedback. You are a role-play character that helps the learner to understand the lesson better. 
Following is the tutor description that learner has provided about the role:
{lesson.tutor_prompt}
Following is the lesson description that learner has provided:
{lesson.lesson_desc}
"""
            sc_history_for_tutor_context = ""
            for conv in all_conversations_db:
                if conv.agent_role == 'sc':
                    sc_history_for_tutor_context += f"learner: {conv.user_input}\nSimu: {conv.response}\n"
            
            final_tutor_system_prompt = tutor_system_prompt_base
            if sc_history_for_tutor_context:
                final_tutor_system_prompt += f"\nFollowing is the conversation so far learner has had with Simu (a complementary role-play character):\n{sc_history_for_tutor_context}"

            messages_for_llm.append({"role": "system", "content": final_tutor_system_prompt})
            for conv in all_conversations_db:
                if conv.agent_role == 'tutor':
                    messages_for_llm.append({"role": "user", "content": conv.user_input})
                    messages_for_llm.append({"role": "assistant", "content": conv.response})
            messages_for_llm.append({"role": "user", "content": user_input})
            chatbot_output = get_chat_response(messages_for_llm)

        elif agent_role == "sc":
            sc_system_prompt = f"""
You are a help assistant. your role is to play a complementary role based on the description provided below. You create an experience scenario for the learner to understand the lesson better.
Following is the role-play description that learner has provided about the role:
{lesson.sc_prompt}
"""
            messages_for_llm.append({"role": "system", "content": sc_system_prompt})
            for conv in all_conversations_db:
                if conv.agent_role == 'sc':
                    messages_for_llm.append({"role": "user", "content": conv.user_input})
                    messages_for_llm.append({"role": "assistant", "content": conv.response})
            messages_for_llm.append({"role": "user", "content": user_input})
            chatbot_output = get_chat_response(messages_for_llm)
        else:
            return jsonify({"error": "Invalid agent role specified."}), 400

        timestamp = datetime.now()
        conversation = ConversationHistory(lesson_id=lessonID, 
                                           user_id=current_user.id, 
                                           user_input=user_input, 
                                           response=chatbot_output,
                                           agent_role=agent_role,
                                           timestamp=timestamp)
        db.session.add(conversation)
        db.session.commit()

        return jsonify({"toUserText": chatbot_output, "timestamp": timestamp.isoformat()})
    
    def clear_chat(self):
        lessonID = request.get_json().get("lessonID")
        # Ensure the lesson exists and belongs to the current user before clearing chat
        lesson = Lesson.query.filter_by(id=lessonID, created_by=current_user.id).first()
        if not lesson:
            return jsonify({"error": "Lesson not found or not authorized."}), 404
            
        ConversationHistory.query.filter_by(lesson_id=lessonID, user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"message": "Chat history cleared successfully.", "toUserText": ""})
