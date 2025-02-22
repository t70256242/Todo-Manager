from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Table, Column, ForeignKey, Enum, DateTime, Boolean, or_, and_
import html
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_bootstrap import Bootstrap5

from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import random
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

scheduler = BackgroundScheduler()

my_email = os.getenv('MY_EMAIL')
my_pass = os.getenv("MY_PASSWORD")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")

UPLOAD_FOLDER = 'static/uploads/profile_pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
ckeditor = CKEditor(app)
Bootstrap5(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# Association table for many-to-many relationship between users and projects
project_users_association = db.Table(
    'project_users',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(Integer, primary_key=True)
    first_name = db.Column(String(250), nullable=False)
    last_name = db.Column(String(250), nullable=False)
    username = db.Column(String(250), nullable=False, unique=True)
    nickname = db.Column(String(250), nullable=True)
    email = db.Column(String(250), nullable=False, unique=True)
    password = db.Column(String(250), nullable=False)
    date_ = db.Column(String(250), nullable=False)
    gender = db.Column(String(250), nullable=True)
    phone = db.Column(String(250), nullable=True)
    address = db.Column(String(250), nullable=True)
    bio = db.Column(String(250), nullable=True)
    profile_picture_path = db.Column(String(250), nullable=True)

    friend_list = relationship("Friends", foreign_keys="Friends.author_id", back_populates="author")
    todo_list = relationship("Todo", back_populates="author")
    projects = relationship("Project", secondary=project_users_association, back_populates="users")
    owned_projects = relationship("Project", back_populates="author")
    birth_dates = relationship("Birthday", back_populates="author")
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic')

    messages = relationship(
        "Message",
        primaryjoin="User.id == Message.author_id",
        back_populates="message_author"
    )
    received_messages = relationship(
        "Message",
        primaryjoin="User.id == Message.recipient_id",
        back_populates="recipient"
    )


class Friends(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    author = relationship("User", foreign_keys=[author_id], back_populates="friend_list")
    friend = relationship("User", foreign_keys=[friend_id])


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.Column(String(250), nullable=True)
    category_id = db.Column(db.Integer, nullable=True)
    read = db.Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            'read': self.read,
            'category': self.category,
            'category_id': self.category_id
        }


class Todo(db.Model):
    __tablename__ = "todo"
    id = db.Column(Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="todo_list")

    task_name = db.Column(String(250), nullable=False)
    description = db.Column(Text)
    priority = db.Column(Enum("high", "medium", "low", name="task_priority_enum"), nullable=False, default="low")
    due_date = db.Column(String(250))
    created_date = db.Column(String(250))
    last_updated = db.Column(String(250))
    assigned_to = db.Column(String(250))
    tags = db.Column(String(250))
    comments = db.Column(Text, nullable=True)
    status = db.Column(Enum("todo", "doing", "done", name="task_status_enum"), nullable=False, default="todo")

    def to_dict(self):
        return {
            "id": self.id,
            "task_name": self.task_name,
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date,
            "created_date": self.created_date,
            "last_updated": self.last_updated,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "comments": self.comments,
            "status": self.status,
            "author": self.author.to_dict() if self.author and hasattr(self.author, "to_dict") else self.author_id,
        }


class ProjectTask(db.Model):
    __tablename__ = "project_tasks"
    id = db.Column(Integer, primary_key=True)

    project_id = db.Column(ForeignKey("project.id"), nullable=False)
    project = relationship("Project", back_populates="tasks")

    project_title = db.Column(String(250), nullable=False)
    task_name = db.Column(String(250), nullable=False)
    description = db.Column(Text, nullable=True)
    priority = db.Column(Enum("high", "medium", "low", name="task_priority_enum"), nullable=False, default="low")
    status = db.Column(Enum("todo", "doing", "done", name="task_status_enum"), nullable=False, default="todo")
    start_date = db.Column(String(250))
    due_date = db.Column(String(250))
    dependencies = db.Column(String(250))
    estimated_time = db.Column(String(250))
    actual_time = db.Column(String(250))
    assigned_to = db.Column(String(250))
    comments = db.Column(Text, nullable=True)


class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(Integer, primary_key=True)

    author_id = db.Column(ForeignKey("users.id"))
    author = relationship("User", back_populates="owned_projects")
    users = relationship("User", secondary=project_users_association, back_populates="projects")

    title = db.Column(String(250), nullable=False)
    description = db.Column(Text)
    start_date = db.Column(String(250))
    end_date = db.Column(String(250))
    comments = db.Column(Text)

    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "comments": self.comments,
            "author": self.author.to_dict() if self.author and hasattr(self.author, "to_dict") else self.author_id,
            "users": [user.to_dict() if hasattr(user, "to_dict") else user.id for user in self.users],
            "tasks": [task.to_dict() if hasattr(task, "to_dict") else task.id for task in self.tasks],
        }


class Birthday(db.Model):
    __tablename__ = "birthdays"
    id = db.Column(Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="birth_dates")

    first_name = db.Column(String(250), nullable=False)
    last_name = db.Column(String(250), nullable=False)
    birth_date = db.Column(String(250), nullable=False)
    message = db.Column(String(250), nullable=True)
    email = db.Column(String(250), nullable=False)
    ignore = db.Column(Enum("true", "false", name="ignore_enum"), nullable=False, default="true")

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "birth_date": self.birth_date,
            "message": self.message,
            "email": self.email,
            "ignore": self.ignore,
            "author": self.author.to_dict() if self.author and hasattr(self.author, "to_dict") else self.author_id,
        }


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(Integer, primary_key=True)

    # Sender (author)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message_author = relationship("User", foreign_keys=[author_id], back_populates="messages")

    # Recipient
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")

    # Message content and metadata
    message_content = db.Column(String(5000), nullable=False)
    timestamp = db.Column(DateTime, default=datetime.utcnow)
    read = db.Column(Boolean, default=False)


with app.app_context():
    db.create_all()


@login_manager.unauthorized_handler
def custom_unauthorized():

    flash("You have to login", "warning")
    return redirect(url_for('login'))


def check_delete_message(message_list):
    for message in message_list:
        conversation_length = len(message[conversation])
        if conversation_length <= 8:
            continue
        else:
            diff = conversation_length - 8
            for i in range(diff):
                oldest_message = conversation[i]
                db.session.delete(oldest_message)
            db.session.commit()
    return message_list


def track_activity(user, message, category, category_id):
    if isinstance(user, int):
        user_id = user
    else:
        user_id = user.id
    notification = Notification(message=message, user_id=user_id, category=category, category_id=category_id)
    db.session.add(notification)
    db.session.commit()


def get_conversation_between_users(user_a_id, user_b_id, order_by=False):
    if order_by:
        messages_ = (
            db.session.query(Message)
            .filter(
                or_(
                    and_(Message.author_id == user_a_id, Message.recipient_id == user_b_id),
                    and_(Message.author_id == user_b_id, Message.recipient_id == user_a_id),
                )
            )
            .order_by(Message.timestamp.desc())
            .all()
        )
        return messages_
    messages_ = (
        db.session.query(Message)
        .filter(
            or_(
                and_(Message.author_id == user_a_id, Message.recipient_id == user_b_id),
                and_(Message.author_id == user_b_id, Message.recipient_id == user_a_id),
            )
        )
        .order_by(Message.timestamp)
        .all()
    )
    return messages_


def check_and_send_birthday_messages():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    with app.app_context():
        all_projects = db.session.execute(db.select(Project)).scalars().all()
        all_todos = db.session.execute(db.select(Todo)).scalars().all()
        all_birthdays = db.session.execute(db.select(Birthday)).scalars().all()

        due_projects = [
            {
                "category": 7,
                "projects": [
                    project for project in all_projects
                    if (datetime.strptime(project.end_date, "%Y-%m-%d") - today).days == 7
                ]
            },
            {
                "category": 3,
                "projects": [
                    project for project in all_projects
                    if (datetime.strptime(project.end_date, "%Y-%m-%d") - today).days == 3
                ]
            },
            {
                "category": 0,
                "projects": [
                    project for project in all_projects
                    if (datetime.strptime(project.end_date, "%Y-%m-%d") - today).days == 0
                ]
            }
        ]

        due_todos = [
            {
                "category": 7,
                "tasks": [
                    todo for todo in all_todos
                    if (datetime.strptime(todo.due_date, "%Y-%m-%d") - today).days == 7
                ]
            },
            {
                "category": 3,
                "tasks": [
                    todo for todo in all_todos
                    if (datetime.strptime(todo.due_date, "%Y-%m-%d") - today).days == 3
                ]
            },
            {
                "category": 0,
                "tasks": [
                    todo for todo in all_todos
                    if (datetime.strptime(todo.due_date, "%Y-%m-%d") - today).days == 0
                ]
            }
        ]

        due_birthdays = [
            {
                "category": 0,
                "birthdays": [
                    birthday for birthday in all_birthdays
                    if (datetime.strptime(birthday.birth_date, "%Y-%m-%d") - today).days == 0
                ]
            }
        ]

        for project in due_projects:
            if project['category'] == 7:

                for pro in project['projects']:

                    track_activity(user=pro.author_id,
                                   message=f"{pro.title.title()} is due in 7 days",
                                   category="project",
                                   category_id=pro.id
                                   )
            elif project['category'] == 3:
                for pro in project['projects']:

                    track_activity(user=pro.author_id,
                                   message=f"{pro.title.title()} is due in 3 days",
                                   category="project",
                                   category_id=pro.id
                                   )
            else:
                for pro in project['projects']:

                    track_activity(user=pro.author_id,
                                   message=f"{pro.title.title()} is due Today!",
                                   category="project",
                                   category_id=pro.id
                                   )

        for todo in due_todos:
            if todo['category'] == 7:
                for to_ in todo['tasks']:
                    track_activity(user=to_.author_id,
                                   message=f"{to_.task_name.title()} is due in 7 days",
                                   category="todo",
                                   category_id=to_.id
                                   )
            elif todo['category'] == 3:
                for to_ in todo['tasks']:
                    track_activity(user=to_.author_id,
                                   message=f"{to_.task_name.title()} is due in 3 days",
                                   category="todo",
                                   category_id=to_.id
                                   )
            else:
                for to_ in todo['tasks']:
                    track_activity(user=to_.author_id,
                                   message=f"{to_.task_name.title()} is due Today!",
                                   category="todo",
                                   category_id=to_.id
                                   )

        for birthday in due_birthdays:
            for b in birthday['birthdays']:
                track_activity(user=b.author_id,
                               message=f"Its {b.first_name.title()}'s Birthday  Today!",
                               category="birthday",
                               category_id=b.id,
                               )
                sender = b.author.nickname or b.author.name
                sender_email = b.author.email
                b_person = b.name
                b_email = b.email

                if b.message is None or not b.message.strip():

                    continue
                else:
                    message = b.message

                try:
                    connection = SMTP("smtp.gmail.com", 587)
                    connection.starttls()
                    connection.login(my_email, my_pass)

                    email_message = (
                        f"Subject: Happy Birthday {b_person}\n"
                        f"From: {my_email}\n"
                        f"To: {b_email}, {sender_email}\n\n"
                        f"Happy Birthday {b_person}!\n\n"
                        f"{message}.\n"
                        f"From: {sender} with love.\n\n\n\n"
                        f"This service is provided by EA Shed Birthday wisher app."
                    )

                    connection.sendmail(
                        from_addr=my_email,
                        to_addrs=[b_email, sender_email],
                        msg=email_message
                    )
                    connection.quit()
                    print('Sent successfully')
                except Exception as e:
                    print(f"Failed to send email to {b_person}: {e}")


scheduler.add_job(check_and_send_birthday_messages, 'cron', hour=0, minute=12)
scheduler.start()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.template_filter('format_date')
def format_date(value):
    """
    Formats a date string (e.g., "2024-12-17") to a desired format (e.g., "May, 22").
    """
    try:
        date_obj = datetime.strptime(value, "%Y-%m-%d")
        return date_obj.strftime("%B, %d")
    except (ValueError, TypeError):
        return value


@app.template_filter('calculate_age')
def calculate_age(birthdate):
    birthdate = datetime.strptime(birthdate, '%Y-%m-%d')
    today = datetime.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))


@app.context_processor
def inject_global_data():
    try:
        if not current_user.is_authenticated:
            return {
                'global_data': {
                    'user': None,
                    'time': datetime.now().strftime("%B %d, %Y"),
                    'projects': 'Guest',
                    'user_name': 'Guest',
                    'todos': 'Guest',
                    'todo_count': 'Guest',
                    'this_month_birthday': 'Guest',
                    'user_sent_messages': 'Guest',
                    'user_received_messages': 'Guest',
                    'notifications': 'Guest',
                    'unread_message': 'Guest',
                    'unread_notifications': 'Guest',
                    'notifications_dict': 'Guest'
                }
            }

        the_user = db.session.execute(
            db.select(User).where(User.id == current_user.id)
        ).scalar()
        the_project = db.session.execute(
            db.select(Project).where(Project.author_id == current_user.id)
        ).scalars().all()
        the_todo = db.session.execute(
            db.select(Todo).where(Todo.author_id == current_user.id)
        ).scalars().all()
        user_received_messages = db.session.execute(
            db.select(Message).where(Message.recipient_id == current_user.id)
        ).scalars().all()
        user_sent_messages = db.session.execute(
            db.select(Message).where(Message.author_id == current_user.id)
        ).scalars().all()
        all_notification = db.session.execute(
            db.select(Notification).where(Notification.user_id == current_user.id)
        ).scalars().all()

        unread_message = [message for message in user_received_messages if message.read is False]
        unread_notifications = [notification for notification in all_notification if notification.read is False]

        notifications_dict = [notification.to_dict() for notification in all_notification]

        task_statuses = [task.status for task in the_todo]
        total_tasks = len(the_todo)

        if total_tasks == 0:
            todo_count = 0
        else:
            status_counts = Counter(task_statuses)

            todo_count = status_counts.get("todo", 0)

        current_day = datetime.now().day
        current_month = datetime.now().month
        current_month_short = datetime.now().strftime("%b")
        all_birthday = db.session.execute(
            db.select(Birthday).where(Birthday.author_id == current_user.id)).scalars().all()
        this_month_birthday = []
        for b in all_birthday:

            b_month = int(b.birth_date.split('-')[1])

            if current_month == b_month:
                if int(b.birth_date.split('-')[-1]) >= current_day and b.ignore == "false":
                    this_month_birthday.append(b.birth_date)

        if the_user is None:
            current_app.logger.warning(f"User with ID {current_user.id} not found in the database.")
            return {
                'global_data': {
                    'user': None,
                    'time': datetime.now().strftime("%B %d, %Y"),
                    'projects': 'Unknown User',
                    'user_name': 'Unknown User',
                    'todos': 'Unknown User',
                    'todo_count': 'Unknown User',
                    'this_month_birthday': 'Unknown User',
                    'user_sent_messages': 'Unknown User',
                    'user_received_messages': 'Unknown User',
                    'notifications': 'Unknown User',
                    'unread_message': 'Unknown User',
                    'unread_notifications': 'Unknown User',
                    'notifications_dict': 'Unknown User'
                }
            }

        return {
            'global_data': {
                'user': the_user,
                'time': datetime.now().strftime("%B %d, %Y"),
                'projects': the_project[:3],
                'user_name': f'{the_user.first_name} {the_user.last_name}',
                'todos': the_todo,
                'todo_count': todo_count,
                'this_month_birthday': len(this_month_birthday),
                'user_sent_messages': user_sent_messages,
                'user_received_messages': user_received_messages,
                'notifications': all_notification,
                'unread_message': unread_message,
                'unread_notifications': unread_notifications,
                'notifications_dict': notifications_dict
            }
        }
    except Exception as e:
        current_app.logger.error(f"Error in context processor: {e}")
        return {
            'global_data': {
                'user': None,
                'time': datetime.now().strftime("%B %d, %Y"),
                'projects': 'Error',
                'user_name': 'Error',
                'todos': 'Error',
                'todo_count': 'Error',
                'this_month_birthday': 'Error',
                'user_sent_messages': 'Error',
                'user_received_messages': 'Error',
                'notifications': 'Error',
                'unread_message': 'Error',
                'unread_notifications': 'Error',
                'notifications_dict': 'Error'
            }
        }


def project_entry(project_ids):
    project_entries = []

    for project_id in project_ids:
        project = db.session.execute(db.select(Project).where(Project.id == project_id)).scalar()
        if not project:
            continue

        task_statuses = [task.status for task in project.tasks]
        total_tasks = len(project.tasks)

        if total_tasks == 0:
            project_entries.append(
                {
                    'title': project.title,
                    'gantt': None,
                    'donut': None,
                    'line': None,
                    'stacked': None,
                    'progress': None
                }
            )
            continue

        # Count task statuses
        status_counts = Counter(task_statuses)

        # Generate Gantt data
        gantt_data = [
            {
                'label': task.task_name,
                'start': datetime.strptime(task.start_date, "%Y-%m-%d").strftime("%Y-%m-%d"),
                'end': datetime.strptime(task.due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            }
            for task in project.tasks
        ]

        # Generate Donut data
        donut_data = {
            "todo": status_counts.get("todo", 0) / total_tasks * 100,
            "doing": status_counts.get("doing", 0) / total_tasks * 100,
            "done": status_counts.get("done", 0) / total_tasks * 100,
        }
        progress = donut_data["done"]

        # Generate Line Chart (Task Status Trend) data
        task_trend = defaultdict(lambda: {"todo": 0, "doing": 0, "done": 0})

        for task in project.tasks:
            for day_offset in range((datetime.strptime(task.due_date, "%Y-%m-%d") - datetime.strptime(task.start_date,
                                                                                                      "%Y-%m-%d")).days + 1):
                date_key = (datetime.strptime(task.start_date, "%Y-%m-%d") + timedelta(days=day_offset)).strftime(
                    "%Y-%m-%d")
                task_trend[date_key][task.status] += 1
        line_data = [
            {"date": date, **status} for date, status in sorted(task_trend.items())
        ]

        # Generate Stacked Bar Chart (Resource Allocation) data
        resource_allocation = defaultdict(lambda: {"todo": 0, "doing": 0, "done": 0})
        for task in project.tasks:
            if task.assigned_to:
                resource_allocation[task.assigned_to][task.status] += 1
        stacked_data = [
            {"team_member": member, **statuses}
            for member, statuses in resource_allocation.items()
        ]

        varies = {
            'title': project.title,
            'gantt': gantt_data,
            'donut': donut_data,
            'line': line_data,
            'stacked': stacked_data,
            'progress': progress
        }

        project_entries.append(varies)
    return project_entries


def project_entry_single(project_id):
    project = db.session.execute(db.select(Project).where(Project.id == project_id)).scalar()
    if not project:
        return None

    task_statuses = [task.status for task in project.tasks]
    total_tasks = len(project.tasks)

    if total_tasks == 0:
        return {
            'title': project.title,
            'gantt': None,
            'donut': None,
            'line': None,
            'stacked': None,
            'progress': None
        }

    # Count task statuses
    status_counts = Counter(task_statuses)

    # Generate Gantt data
    gantt_data = [
        {
            'label': task.task_name,
            'start': datetime.strptime(task.start_date, "%Y-%m-%d").strftime("%Y-%m-%d"),
            'end': datetime.strptime(task.due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        }
        for task in project.tasks
    ]

    # Generate Donut data
    donut_data = {
        "todo": status_counts.get("todo", 0) / total_tasks * 100,
        "doing": status_counts.get("doing", 0) / total_tasks * 100,
        "done": status_counts.get("done", 0) / total_tasks * 100,
    }
    progress = donut_data["done"]

    # Generate Line Chart (Task Status Trend) data
    task_trend = defaultdict(lambda: {"todo": 0, "doing": 0, "done": 0})

    for task in project.tasks:
        for day_offset in range((datetime.strptime(task.due_date, "%Y-%m-%d") - datetime.strptime(task.start_date,
                                                                                                  "%Y-%m-%d")).days + 1):
            date_key = (datetime.strptime(task.start_date, "%Y-%m-%d") + timedelta(days=day_offset)).strftime(
                "%Y-%m-%d")
            task_trend[date_key][task.status] += 1
    line_data = [
        {"date": date, **status} for date, status in sorted(task_trend.items())
    ]

    # Generate Stacked Bar Chart (Resource Allocation) data
    resource_allocation = defaultdict(lambda: {"todo": 0, "doing": 0, "done": 0})
    for task in project.tasks:
        if task.assigned_to:  # Assume task.assigned_to gives the resource (e.g., team member)
            resource_allocation[task.assigned_to][task.status] += 1
    stacked_data = [
        {"team_member": member, **statuses}
        for member, statuses in resource_allocation.items()
    ]

    return {
        'title': project.title,
        'gantt': gantt_data,
        'donut': donut_data,
        'line': line_data,
        'stacked': stacked_data,
        'progress': progress
    }


@app.route('/project-progress', methods=['GET'])
def project_progress():
    project_ids = [
        project.id
        for project in db.session.query(Project).filter_by(author_id=current_user.id).all()
    ]

    get_project_entry = project_entry(project_ids)

    return jsonify(get_project_entry)


@app.route("/events")
def events():
    events_ = []
    all_project = []
    result = db.session.execute(db.select(Project).where(Project.author_id == current_user.id))
    all_project = result.scalars().all()
    for pro in all_project:

        events_.append({"date": pro.end_date, "title": f"{pro.title.title()} Due Date", "type": "projects"})

    all_todo = []
    result = db.session.execute(db.select(Todo).where(Todo.author_id == current_user.id))
    if result is not None:
        all_todo = result.scalars().all()
    for to in all_todo:

        events_.append({"date": to.due_date, "title": f"{to.task_name.title()} Due Date", "type": "todos"})

    all_birthday = []
    result = db.session.execute(db.select(Birthday).where(Birthday.author_id == current_user.id))
    all_birthday = result.scalars().all()
    for b in all_birthday:

        events_.append({"date": b.birth_date, "title": f"{b.first_name.title()}'s Birthday", "type": "birthdays"})

    return jsonify(events_)


def to_dict(self):
    return {col.name: getattr(self, col.name) for col in self.__table__.columns}


@app.route('/fetch-user/<username>', methods=['GET'])
def fetch_user(username):
    try:
        the_user = db.session.execute(db.select(User).where(User.username == username)).scalar()
        return jsonify(
            {
                'id': the_user.id,
                'username': the_user.username
            }
        )
    except:
        return jsonify({"error": "User not found"}), 404


@app.route('/search/<topic>', methods=['POST'])
def search_items(topic):
    try:
        search_term = request.json.get('query', '')
        if not search_term:
            flash("No search term provided", 'warning')
            referrer = request.referrer
            if referrer:
                return redirect(referrer)
            else:

                return redirect(url_for('dashboard'))

        search_term = f"%{search_term}%"

        results = []

        if topic == "projects":
            results = Project.query.filter(
                (Project.title.like(search_term)) |
                (Project.description.like(search_term)) |
                (Project.comments.like(search_term))
            ).all()

        elif topic == "tasks":
            results = Todo.query.filter(
                (Todo.task_name.like(search_term)) |
                (Todo.description.like(search_term)) |
                (Todo.tags.like(search_term)) |
                (Todo.comments.like(search_term))
            ).all()

        elif topic == "birthdays":
            results = Birthday.query.filter(
                (Birthday.first_name.like(search_term)) |
                (Birthday.last_name.like(search_term))
            ).all()

        else:
            return jsonify({"error": "Invalid topic"}), 400

        formatted_results = [
            result.to_dict() for result in results
        ]

        return jsonify({"results": formatted_results}), 200

    except Exception as e:
        current_app.logger.error(f"Error in search_items: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500


def get_friends(user_id):
    m_list = []

    im_friend = db.session.execute(db.select(Friends).where(Friends.author_id == user_id)).scalars().all()

    for f in im_friend:
        m_list.append(f.friend_id)
    friends = []
    for m in m_list:
        the_friend = db.session.execute(db.select(User).where(User.id == m)).scalar()
        friends.append(the_friend)
    return friends


@app.route('/check_password/<username>', methods=['POST'])
def check_password(username):
    try:
        the_user = db.session.execute(
            db.select(User).where(User.username == username)
        ).scalar()

        if not the_user:
            return jsonify({"error": "User not found"}), 404

        password = request.json.get('password')
        if not password:
            return jsonify({"error": "Password is required"}), 400

        if check_password_hash(the_user.password, password):
            return jsonify({"success": "Password correct"}), 200
        else:
            return jsonify({"error": "Incorrect Password"}), 400

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route('/update_user_info/<int:user_id>', methods=['POST'])
def update_user_info(user_id):
    try:
        user = db.session.execute(
            db.select(User).where(User.id == user_id)
        ).scalar()

        if not user:
            return jsonify({"error": "User not found"}), 404

        nickname = request.form.get('nickname')
        birthday = request.form.get('birthday')
        phone = request.form.get('phone')
        address = request.form.get('address')
        bio = request.form.get('bio')

        if nickname:
            user.nickname = nickname
        if birthday:
            user.date_ = birthday
        if phone:
            user.phone = phone
        if address:
            user.address = address
        if bio:
            user.bio = bio

        db.session.commit()
        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/add_user', methods=["POST"])
def add_user():
    the_user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
    form_id = request.form.get('form_id')

    if form_id == 'form1':
        with app.app_context():
            the_friend = db.session.execute(
                db.select(User).where(
                    User.username == request.form.get('friend_username'))).scalar()
            new_friend = Friends(
                author_id=current_user.id,
                friend_id=the_friend.id
            )

            db.session.add(new_friend)
            db.session.commit()
            track_activity(
                user=the_friend.id,
                message=f"{the_user.first_name.title()} added you as friend",
                category="friend",
                category_id=current_user.id
            )
        return redirect(request.referrer)

    try:
        connection = SMTP("smtp.gmail.com")
        connection.starttls()
        connection.login(my_email, my_pass)

        # Create email content with UTF-8 encoding
        subject = "Invitation to Join Our Platform"
        body = (
            "I hope this message finds you well. I would like to extend an invitation for you to join our team on "
            "[Platform/Tool Name]. This platform will allow us to collaborate effectively, track progress, "
            "and manage our tasks seamlessly. Please use the following link to sign up and get started: "
            "[Insert Invite Link]. "
            "If you encounter any issues during the sign-up process or have any questions, please don’t hesitate "
            "to reach out. I’ll be happy to assist. We look forward to having you on board and "
            f"collaborating with you. Best regards, {the_user.first_name} {the_user.last_name}."
        )

        # Use MIMEMultipart for richer email content
        email_message = MIMEMultipart()
        email_message["Subject"] = subject
        email_message["From"] = my_email
        email_message["To"] = request.form.get("friend_email")

        # Attach the email body
        email_message.attach(MIMEText(body, "plain", "utf-8"))

        # Send the email
        connection.sendmail(
            from_addr=my_email,
            to_addrs=[request.form.get("friend_email"), my_email],
            msg=email_message.as_string()
        )
        print("Email sent successfully")
        connection.quit()
        return redirect(request.referrer)
    except Exception as e:
        print(f"Failed to send email to {request.form.get('friend_email')}: {e}")
        return redirect(request.referrer)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload-profile-picture/<int:user_id>', methods=['POST'])
def upload_profile_picture(user_id):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_id}_{filename}")
        file_path = file_path.replace("\\", "/")

        file.save(file_path)

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.profile_picture_path = file_path
        db.session.commit()

        return jsonify({"message": "Profile picture uploaded successfully!", "file_path": file_path}), 200

    return jsonify({"error": "File type not allowed"}), 400


@app.route('/update_notification/<int:notification_id>', methods=['POST'])
def update_notification(notification_id):
    notification = db.session.execute(db.select(Notification).where(Notification.id == notification_id)).scalar()
    if notification:
        notification.read = True
        db.session.commit()
        return jsonify({"success": True}), 200
    return jsonify({"error": "Notification not found"}), 404


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    all_project = []
    result = db.session.execute(db.select(Project).where(Project.author_id == current_user.id))
    all_project = result.scalars().all()

    all_todo = []
    result = db.session.execute(db.select(Todo).where(Todo.author_id == current_user.id))
    if result is not None:
        all_todo = result.scalars().all()

    all_birthday = []
    result = db.session.execute(db.select(Birthday).where(Birthday.author_id == current_user.id))
    all_birthday = result.scalars().all()

    return render_template('dashboard.html',
                           projects=all_project,
                           todos=all_todo,
                           birthdays=all_birthday
                           )


@app.route('/projects')
@login_required
def project_list():
    all_project = []
    result = db.session.execute(db.select(Project).where(Project.author_id == current_user.id))
    all_project = result.scalars().all()
    project_ids = []
    for pro in all_project:
        project_ids.append(pro.id)

    project_entries = project_entry(project_ids)
    progressive = {}
    count = 0
    for entry in project_entries:
        if entry['progress'] is not None:
            progressive[project_ids[count]] = {
                'progress': round(entry['progress'])
            }

        else:
            progressive[project_ids[count]] = {
                'progress': None
            }
        count += 1

    return render_template('project-list.html', projects=all_project, progress=progressive)


@app.route('/project/<int:number>', methods=['GET', 'POST'])
@login_required
def project_select(number):
    the_project = db.get_or_404(Project, number)

    project_data = project_entry_single(the_project.id)

    friends = get_friends(current_user.id)

    return render_template('project-select.html',
                           project=the_project,
                           project_data=project_data,
                           friends_list=friends
                           )


@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    if request.method == "POST":
        the_project = db.session.execute(db.select(Project).where(Project.id == project_id)).scalar_one_or_none()
        the_project.title = request.form.get('editProjectTitle')
        the_project.description = request.form.get('editProjectDescription')
        the_project.start_date = request.form.get('editProjectStartDate')
        the_project.end_date = request.form.get('editProjectDueDate')
        the_project.comments = request.form.get('editProjectComments')
        db.session.commit()
        return redirect(url_for('project_list'))
    project = db.get_or_404(Project, project_id)
    if project:
        return jsonify({
            "editProjectTitle": project.title,
            "editProjectDescription": project.description,
            "editProjectStartDate": project.start_date,
            "editProjectDueDate": project.end_date,
            "editProjectComments": project.comments,
        })
    return jsonify({"error": "Task not found"}), 404


@app.route('/delete_project/<int:project_id>', methods=['GET'])
@login_required
def delete_project(project_id):
    the_project = db.get_or_404(Project, project_id)
    db.session.delete(the_project)
    db.session.commit()
    return redirect(url_for('project_list'))


@app.route('/get-task-details/<int:task_id>', methods=['GET'])
@login_required
def get_task_details(task_id):
    task = db.get_or_404(ProjectTask, task_id)
    if task:
        return jsonify({
            "projectTitle": task.project.title,
            "taskSelectName": task.task_name,
            "taskSelectDescription": task.description,
            "taskSelectPriority": task.priority,
            "taskSelectStatus": task.status,
            "assignedToTaskSelect": task.assigned_to,
            "startTaskSelectDate": task.start_date,
            "dueTaskSelectDate": task.due_date,
            "taskSelectDependencies": task.dependencies,
            "estimatedTimeTaskSelect": task.estimated_time.split('-')[0],
            "timeRangeTaskSelect": task.estimated_time.split('-')[1],
            "actualTimeTaskSelect": task.actual_time,
            "taskSelectComments": task.comments,
        })
    return jsonify({"error": "Task not found"}), 404


@app.route('/save_task_details/<int:project_id>/<int:task_id>', methods=['POST'])
@login_required
def save_task_details(task_id, project_id):
    task = db.session.execute(db.select(ProjectTask).where(ProjectTask.id == task_id)).scalar_one_or_none()
    task.description = request.form.get("taskSelectDescription")
    task.priority = request.form.get("taskSelectPriority")
    task.status = request.form.get("taskSelectStatus")
    task.start_date = request.form.get("startTaskSelectDate")
    task.due_date = request.form.get("dueTaskSelectDate")
    task.dependencies = request.form.get("taskSelectDependencies") if request.form.get("taskSelectDependencies") else ""
    task.estimated_time = f'{request.form.get("estimatedTimeTaskSelect")} - {request.form.get("timeRangeTaskSelect")}'
    task.comments = request.form.get("taskSelectComments")
    task.assigned_to = request.form.get('assignedToTaskSelect') if request.form.get('assignedToTaskSelect') else ""
    if request.form.get('assignedToTaskSelect'):
        the_user = request.form.get('assignedToTaskSelect')
        user_ = db.session.execute(db.select(User).where(User.username == the_user)).scalar()
        if fetch_user(the_user):
            the_project = db.session.execute(db.select(Project).where(Project.id == project_id)).scalar()
            the_project.users.append(user_)
            track_activity(user_.id,
                           f"{current_user.first_name} added you to {the_project.title}",
                           'project',
                           the_project.id)

    db.session.commit()

    return redirect(url_for('project_select', number=project_id))


@app.route('/delete_project_task/<int:task_id>/<int:project_id>', methods=['GET', 'POST'])
@login_required
def delete_project_task(task_id, project_id):
    the_task = db.get_or_404(ProjectTask, task_id)
    db.session.delete(the_task)
    db.session.commit()
    return redirect(url_for('project_select', number=project_id))


@app.route('/add-project', methods=['POST'])
@login_required
def add_project():
    if request.method == "POST":


        referrer_url = request.referrer

        with app.app_context():
            the_user = db.session.execute(db.select(User).where(User.id == current_user.id)).scalar()
            new_project = Project(
                author_id=current_user.id,
                title=request.form.get('projectTitle'),
                description=request.form.get('description'),
                start_date=request.form.get('startDate'),
                end_date=request.form.get('dueDate'),
                comments=request.form.get('comments')

            )
            new_project.users.append(the_user)
            db.session.add(new_project)
            db.session.commit()

        if "dashboard" in str(referrer_url):
            return redirect(url_for('dashboard'))
        return redirect(url_for('project_list'))


@app.route('/add_project_task/<int:number>', methods=['GET', 'POST'])
@login_required
def add_project_task(number):
    the_project = db.session.execute(db.select(Project).where(Project.id == number)).scalar()

    if request.method == 'POST':

        new_task = ProjectTask(
            project_id=number,
            project_title=the_project.title,
            task_name=request.form.get('taskName'),
            description=request.form.get('taskDescription'),
            priority=request.form.get('priority'),
            start_date=request.form.get('startTaskDate'),
            due_date=request.form.get('dueTaskDate'),
            dependencies=request.form.get('dependencies') if request.form.get('dependencies') else "",
            estimated_time=f"{request.form.get('estimatedTime')} - {request.form.get('timeRange')}",
            actual_time=datetime.utcnow(),
            assigned_to=request.form.get('assignedTo') if request.form.get('assignedTo') else "",
            comments=request.form.get('taskComments'),
            status=request.form.get('status'),
        )
        if request.form.get('assignedTo'):
            the_user = request.form.get('assignedTo')
            user_ = db.session.execute(db.select(User).where(User.username == the_user)).scalar()
            track_activity(user_.id,
                           f"{current_user.first_name} added you to {the_project.title}",
                           'project',
                           the_project.id)
            if fetch_user(the_user):
                the_project.users.append(user_)

        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('project_select', number=number))


@app.route('/todo')
@login_required
def todo_list():
    all_todo = []
    result = db.session.execute(db.select(Todo).where(Todo.author_id == current_user.id))
    all_todo = result.scalars().all()

    return render_template('task-list.html', todos=all_todo)


@app.route('/add_todo_task', methods=['GET', 'POST'])
@login_required
def add_todo_task():
    if request.method == 'POST':
        new_task = Todo(
            author_id=current_user.id,
            task_name=request.form.get('taskName'),
            description=request.form.get('taskDescription'),
            priority=request.form.get('priority'),
            due_date=request.form.get('dueTaskDate'),
            created_date=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            assigned_to=request.form.get('assignedTo'),
            tags=request.form.get('tags'),
            comments=request.form.get('taskComments'),
            status=request.form.get('status'),
        )
        db.session.add(new_task)
        db.session.commit()
        if str(request.referrer).split('/')[-1] == 'todo':
            return redirect(url_for('todo_list'))
    return redirect(url_for('dashboard'))


@app.route('/get-todo-details/<int:todo_id>', methods=['GET'])
@login_required
def get_todo_details(todo_id):
    todo = db.get_or_404(Todo, todo_id)
    if todo:
        return jsonify({
            "taskEditName": todo.task_name,
            "taskEditDescription": todo.description,
            "taskEditPriority": todo.priority,
            "dueTaskEditDate": todo.due_date,
            "taskEditAssignedTo": todo.assigned_to,
            "taskEditTags": todo.tags,
            "taskEditComments": todo.comments,
            "taskEditStatus": todo.status,
        })
    return jsonify({"error": "Task not found"}), 404


@app.route('/todo_edit_save/<int:todo_id>', methods=['GET', 'POST'])
@login_required
def todo_edit_save(todo_id):
    the_todo = db.session.execute(db.select(Todo).where(Todo.id == todo_id)).scalar()
    the_todo.task_name = request.form.get("taskEditName")
    the_todo.description = request.form.get("taskEditDescription")
    the_todo.priority = request.form.get("taskEditPriority")
    the_todo.due_date = request.form.get("dueTaskEditDate")
    the_todo.assigned_to = request.form.get("taskEditAssignedTo")
    the_todo.tags = request.form.get("taskEditTags")

    the_todo.comments = request.form.get("taskEditComments")
    the_todo.status = request.form.get("taskEditStatus")
    db.session.commit()
    return redirect(url_for('todo_list'))


@app.route('/change_todo_status/<int:todo_id>', methods=['GET', 'POST'])
@login_required
def change_todo_status(todo_id):
    the_todo = db.session.execute(db.select(Todo).where(Todo.id == todo_id)).scalar()
    if the_todo.status == "todo":
        the_todo.status = "doing"
    else:
        the_todo.status = "done"
    db.session.commit()
    return redirect(url_for('todo_list'))


@app.route('/delete_todo/<int:todo_id>', methods=['GET', 'POST'])
@login_required
def delete_todo(todo_id):
    the_todo = db.get_or_404(Todo, todo_id)
    db.session.delete(the_todo)
    db.session.commit()
    return redirect(url_for('todo_list'))


@app.route('/add_birth_date', methods=['GET', 'POST'])
@login_required
def add_birth_date():
    if request.method == 'POST':
        new_birth_date = Birthday(
            author_id=current_user.id,
            first_name=request.form.get('birthFirstName'),
            last_name=request.form.get('birthLastName'),
            birth_date=request.form.get('birthDate'),
            ignore='false',
            message=request.form.get('birthDateMessage'),
            email=request.form.get('birthEmail'),

        )
        db.session.add(new_birth_date)
        db.session.commit()
        if str(request.referrer).split('/')[-1] == 'birthdays':
            return redirect(url_for('birthday_list'))
    return redirect(url_for('dashboard'))


@app.route('/add_birth_date_message/<int:number>', methods=['GET', 'POST'])
@login_required
def add_birth_date_message(number):
    if request.method == 'POST':
        with app.app_context():
            the_birthday = db.session.execute(db.select(Birthday).where(Birthday.id == number)).scalar()
            the_birthday.message = request.form.get('birthDateMessageAdd')
            db.session.commit()
        if str(request.referrer).split('/')[-1] == 'birthdays':
            return redirect(url_for('birthday_list'))
    return redirect(url_for('dashboard'))


@app.route('/ignore_birth_date/<int:number>', methods=['GET', 'POST'])
@login_required
def ignore_birth_date(number):
    with app.app_context():
        the_birthday = db.session.execute(db.select(Birthday).where(Birthday.id == number)).scalar()
        if the_birthday.ignore == 'true':
            the_birthday.ignore = 'false'
        else:
            the_birthday.ignore = 'true'
        db.session.commit()

        if str(request.referrer).split('/')[-1] == 'birthdays':
            return redirect(url_for('birthday_list'))
    return redirect(url_for('dashboard'))


@app.route('/birthdays')
@login_required
def birthday_list():
    all_birthday = []
    this_month_birthday = []
    current_day = datetime.now().day
    current_month = datetime.now().month
    current_month_short = datetime.now().strftime("%b")
    result = db.session.execute(db.select(Birthday).where(Birthday.author_id == current_user.id))
    all_birthday = result.scalars().all()
    sorted_birthdays = sorted(all_birthday,
                              key=lambda b: ((int(b.birth_date[5:7]) - current_month) % 12,
                                             int(b.birth_date[8:10]))
                              )
    if len(all_birthday) <= 0:
        return render_template('birthday-list.html')

    else:
        for b in all_birthday:

            b_month = int(b.birth_date.split('-')[1])

            if current_month == b_month:
                if int(b.birth_date.split('-')[-1]) >= current_day and b.ignore == "false":
                    this_month_birthday.append(b.birth_date)
            sorted_dates = sorted(this_month_birthday, key=lambda date: int(date.split("-")[-1]))

        return render_template('birthday-list.html',
                               birthdays=sorted_birthdays,
                               this_month_birthday=sorted_dates,
                               current_day=current_day,
                               current_month_short=current_month_short)


@app.route('/get-birth-details/<int:birth_id>', methods=['GET'])
@login_required
def get_birth_details(birth_id):
    birth = db.get_or_404(Birthday, birth_id)
    if birth:
        return jsonify({
            "birthEditFirstName": birth.first_name,
            "birthEditLastName": birth.last_name,
            "birthEditDate": birth.birth_date,
            "birthEditMessage": birth.message,
            "birthEditEmail": birth.email,
            "birthEditIgnore": birth.ignore,

        })
    return jsonify({"error": "Birthday not found"}), 404


@app.route('/birth_edit_save/<int:birth_id>', methods=['POST'])
@login_required
def birth_edit_save(birth_id):
    the_birth = db.session.execute(db.select(Birthday).where(Birthday.id == birth_id)).scalar()
    the_birth.first_name = request.form.get("birthEditFirstName")
    the_birth.last_name = request.form.get("birthEditLastName")
    the_birth.birth_day = request.form.get("birthEditDate")
    the_birth.message = request.form.get("birthEditMessage")
    the_birth.email = request.form.get("birthEditEmail")
    the_birth.ignore = request.form.get("birthEditIgnore")
    db.session.commit()
    return redirect(url_for('birthday_list'))


@app.route('/calender')
@login_required
def calender_list():
    return render_template('calender-list.html')


@app.route('/charts')
@login_required
def chart_list():
    return render_template('chart-list.html')


@app.route('/friend-list')
@login_required
def friends_list():
    friends = get_friends(current_user.id)
    return render_template('friend-list.html', friends_list=friends)


@app.route('/delete-friend/<int:friend_id>', methods=['GET', 'POST'])
@login_required
def delete_friend(friend_id):
    the_friend = db.session.execute(
        db.select(Friends).where(
            and_(
                Friends.friend_id == friend_id,
                Friends.author_id == current_user.id
            )
        )
    ).scalar()
    if the_friend:
        db.session.delete(the_friend)
        db.session.commit()
    return redirect(url_for('friends_list'))


@app.route('/messages')
@login_required
def messages():
    friend_list = []
    im_sender = db.session.execute(db.select(Message).where(Message.author_id == current_user.id)).scalars().all()
    if im_sender:
        for message in im_sender:
            if message.recipient_id in friend_list:
                continue
            else:
                friend_list.append(message.recipient_id)

    im_receiver = db.session.execute(db.select(Message).where(Message.recipient_id == current_user.id)).scalars().all()
    if im_receiver:
        for message in im_receiver:
            if message.author_id in friend_list:
                continue
            else:
                friend_list.append(message.author_id)

    if len(friend_list) <= 0:
        return render_template('messages-list.html')

    message_list = []

    for recipient in friend_list:
        the_recipient = db.session.execute(db.select(User).where(User.id == recipient)).scalar()
        conversation = get_conversation_between_users(current_user.id, recipient, order_by=True)
        message_list.append(
            {
                'time_stamp': conversation[0].timestamp,
                'recipient': the_recipient,
                'conversation': conversation})

    message_list = sorted(message_list, key=lambda x: x['time_stamp'], reverse=True)
    message_list = check_delete_message(message_list)
    
    return render_template('messages-list.html', message_list=message_list, current_user=current_user)


@app.route('/messages/<int:message_id>')
@login_required
def message_select(message_id):
    the_message = db.session.execute(db.select(Message).where(Message.id == message_id)).scalar()
    # the_message.read = True
    # db.session.commit()
    user_1 = the_message.author_id
    user_2 = the_message.recipient_id
    conversation = get_conversation_between_users(user_1, user_2)
    for co in conversation:

        if co.recipient_id is current_user.id:
            r_message = db.session.execute(db.select(Message).where(Message.id == co.id)).scalar()
            r_message.read = True
            db.session.commit()
    recipient_id = 0
    if user_1 == current_user.id:
        recipient_id = user_2
    else:
        recipient_id = user_1

    the_recipient = db.session.execute(db.select(User).where(User.id == recipient_id)).scalar()

    return render_template('message-select.html',
                           conversation=conversation,
                           current_user=current_user,
                           recipient_id=recipient_id,
                           recipient=the_recipient,
                           message_id=the_message.id)


@app.route('/send_message/<recipient>', methods=['POST'])
@login_required
def send_message(recipient):
    recipient_ = db.session.execute(db.select(User).where(User.username == recipient)).scalar()
    recipient_id = recipient_.id
    source = request.form.get('source', 'unknown')  # Default to 'unknown'

    if source == "modal":
        new_message = Message(
            author_id=current_user.id,
            recipient_id=recipient_id,
            message_content=request.form.get('sendMessageMessage'),
            timestamp=datetime.utcnow(),
            read=False
        )
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('friends_list'))

    if str(request.referrer).split('/')[-1] == 'messages':
        if request.method == 'POST':
            new_message = Message(
                author_id=current_user.id,
                recipient_id=recipient_id,
                message_content=request.form.get('sendMessageMessage'),
                timestamp=datetime.utcnow(),
                read=False
            )
            db.session.add(new_message)
            db.session.commit()
        return redirect(url_for('messages'))

    message_id = str(request.referrer).split('/')[-1]
    if request.method == 'POST':
        new_message = Message(
            author_id=current_user.id,
            recipient_id=recipient_id,
            message_content=request.form.get('message-input'),
            timestamp=datetime.utcnow(),
            read=False
        )
        db.session.add(new_message)
        db.session.commit()
    return redirect(url_for('message_select', message_id=int(message_id)))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')

        with app.app_context():
            user_log = db.session.execute(db.select(User).where(User.email == email)).scalar()
            if user_log is None:
                flash("This email is not registered", "warning")
                return redirect(url_for('login'))
            else:
                if check_password_hash(user_log.password, request.form.get('password')):
                    login_user(user_log)
                    print("logging in...........")
                    return redirect(url_for('dashboard'))
                else:
                    flash("The password is incorrect", "danger")
                    return redirect(url_for('login'))
    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/register', methods=['POST', 'GET'])
def register():

    if request.method == "POST":

        with app.app_context():
            if db.session.execute(db.select(User).where(User.email == request.form.get('email'))).scalar() is None:

                if db.session.execute(
                        db.select(User).where(User.username == request.form.get('username'))).scalar() is None:
                    new_user = User(
                        first_name=request.form.get('firstName'),
                        last_name=request.form.get('lastName'),
                        email=request.form.get('email'),
                        password=generate_password_hash(
                            request.form.get('password'),
                            method=os.getenv('SALT_METHOD'),
                            salt_length=8),
                        date_=f"{request.form.get('day')}-{request.form.get('month')}-{request.form.get('year')}",
                        gender=request.form.get('gender'),
                        nickname=request.form.get('nickname'),
                        username=request.form.get('username'),
                        bio=request.form.get('bio'),
                        phone=request.form.get('phone'),
                        address=request.form.get('address')
                    )
                    print("successful")
                    db.session.add(new_user)
                    db.session.commit()
                    flash("Successfully registered, now login", "success")
                    return redirect(url_for('login'))
                else:
                    flash(f"{request.form.get('username')} already exist, try another username", "info")
                    return redirect(url_for('register'))
            else:
                flash("You already registered with this email, login instead.", "info")
                return redirect(url_for('login'))

    return render_template("register.html", logged_in=current_user.is_authenticated, )


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        the_user = db.session.execute(db.select(User).where(User.username == request.form.get('username'))).scalar()
        if the_user:
            if request.form.get('password') == request.form.get('re_password'):
                the_user.password = generate_password_hash(request.form.get('password'), method=os.getenv('SALT_METHOD'),
                                                           salt_length=8)
                db.session.commit()
                flash('Password changed Successfully', 'success')
                return redirect(url_for('login'))
            else:
                flash('Password does not match', 'error')
                return redirect(url_for('reset_password'))
        else:
            flash('Incorrect username or User dont exist', 'error')
            return redirect(url_for('reset_password'))

    return render_template('reset-password.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == "POST":
        connection = SMTP("smtp.gmail.com")
        connection.starttls()
        connection.login(my_email, my_pass)
        connection.sendmail(
            from_addr=my_email,
            to_addrs=my_email,
            msg=f"{request.form.get('subject')}\n\n"
                f"{request.form.get('message')}.\nAccount Details:\n"
                f"Name: {request.form.get('name')}\n"
                f"Email: {request.form.get('email')}")
        connection.quit()
        flash("🎉 Thank you for reaching out to us! We’ve received your message and and our team "
              "will swoop in with a reply ASAP. Stay tuned!", "success")
        return redirect(url_for('home'))

    return redirect(url_for('home'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True, port=5002)
