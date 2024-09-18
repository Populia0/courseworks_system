from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from django.conf import settings
from .models import CustomUser, Teacher, Student, Course, Application, Topic
from django.db.models import Q
import requests

EMAIL, SEND_TEACHER_CHOICES, TEACHER_CALLBACK, SEND_TOPIC_CALLBACK, PROPOSE_TOPIC, CONFIRM_TOPIC, BUTTON_HANDLER = range(7)

def start(update: Update, context):
    update.message.reply_text("Пожалуйста, введите вашу почту.")
    return EMAIL

def process_email(update, context):
    email = update.message.text
    try:
        custom_user = CustomUser.objects.get(email=email)
        custom_user.telegram_chat_id = update.message.from_user.id
        custom_user.save()
        context.user_data['user'] = custom_user
        if custom_user.is_student != True:
            update.message.reply_text(f"Здравствуйте, {custom_user.first_name}! Ожидайте заявок от студентов")
        elif custom_user.is_student:
            course = custom_user.student.course
            # Найти всех преподавателей курса студента
            teachers = Teacher.objects.filter(courses=course).distinct()

            # Создание кнопок для каждого преподавателя
            keyboard = []
            for teacher in teachers:
                keyboard.append([
                    InlineKeyboardButton(teacher.user.get_full_name(), callback_data=f'teacher_{teacher.id}')
                ])

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(f'Здравствуйте, {custom_user.first_name}! Выберите преподавателя:', reply_markup=reply_markup)
            return TEACHER_CALLBACK
    except:
            update.message.reply_text('Почта не найдена. Попробуйте снова')
            
def send_teacher_choices(update: Update, context):
    student = context.user_data['user']
    course = student.student.course
    teachers = Teacher.objects.filter(courses=course).distinct()

    # Создание inline-кнопок для каждого преподавателя
    keyboard = []
    for teacher in teachers:
        keyboard.append([
            InlineKeyboardButton(teacher.user.get_full_name(), callback_data=f'teacher_{teacher.id}')
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(f'Здравствуйте, {student.first_name}! Выберите преподавателя:', reply_markup=reply_markup)
    return TEACHER_CALLBACK

def teacher_callback(update: Update, context):
    query = update.callback_query
    query.answer()

    teacher_id = query.data.split('_')[1]
    teacher = Teacher.objects.get(id=teacher_id)

    topics = Topic.objects.filter(teacher=teacher)
    available_spots = teacher.max_students - Application.objects.filter(Q(teacher=teacher) & Q(is_approved=True)).count()

    keyboard = [
        [InlineKeyboardButton('Отправить тему', callback_data=f'send_topic_{teacher_id}')],
        [InlineKeyboardButton('Предложить свою тему', callback_data=f'propose_topic_{teacher_id}')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = f"Преподаватель: {teacher.user.get_full_name()}\n"
    message_text += f"Доступные темы:\n"
    for topic in topics:
        message_text += f" - {topic.name}\n"
    message_text += f"\nCлoты: {available_spots}"

    query.edit_message_text(text=message_text, reply_markup=reply_markup)
    return SEND_TOPIC_CALLBACK

def send_topic_callback(update: Update, context):
    query = update.callback_query
    query.answer()

    # Получаем callback_data
    callback_data = query.data

    if callback_data.startswith('send_topic_'):
            query = update.callback_query
            query.answer()

            teacher_id = query.data.split('_')[2]
            teacher = Teacher.objects.get(id=teacher_id)

            context.user_data['teacher'] = teacher

            # Получить темы преподавателя
            topics = Topic.objects.filter(teacher=teacher)
            keyboard = []
            for topic in topics:
                keyboard.append([InlineKeyboardButton(topic.name, callback_data=f'choose_topic_{topic.id}')])

            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text('Выберите тему:', reply_markup=reply_markup)

            query = update.callback_query
            query.answer()

            # Получаем ID темы
            topic_id = query.data.split('_')[2]
            topic = Topic.objects.get(id=topic_id)
            student = context.user_data['user'].student

            # Создание заявки
            Application.objects.create(student=student, teacher=topic.teacher, topic=topic)
            teacher = CustomUser.objects.get(teacher=topic.teacher)
            # Отправляем уведомление преподавателю на почту и в Telegram
            send_email_to_teacher(teacher, topic, context.user_data['user'])
            send_telegram_message(teacher, context.user_data['user'], topic, context)

            query.edit_message_text(f"Заявка на тему '{topic.name}' отправлена на рассмотрение.")

            return ConversationHandler.END
    elif callback_data.startswith('propose_topic_'):
            query = update.callback_query
            query.answer()

            teacher_id = query.data.split('_')[2]
            teacher = Teacher.objects.get(id=teacher_id)

            context.user_data['teacher'] = teacher

            query.message.edit_text('Введите название темы:')
            return PROPOSE_TOPIC

def propose_topic(update: Update, context):
    topic = update.message.text
    teacher = context.user_data['teacher']

    topic = Topic.objects.create(name=topic, teacher=teacher)
    student = context.user_data['user'].student

    # Создание заявки
    Application.objects.create(student=student, teacher=topic.teacher, topic=topic)
    teacher = CustomUser.objects.get(teacher=topic.teacher)
    # Отправляем уведомление преподавателю на почту и в Telegram
    send_email_to_teacher(teacher, topic, context.user_data['user'])
    send_telegram_message(teacher, context.user_data['user'], topic, context)

    update.message.reply_text(f"Заявка на тему '{topic.name}' отправлена на рассмотрение.")
    return ConversationHandler.END


from django.core.mail import send_mail
from django.conf import settings

def send_email_to_teacher(teacher, topic, student, proposed_topic=None):
    subject = f"Новая заявка от студента {student.first_name} {student.last_name}"
    if proposed_topic:
        message = f"Студент {student.first_name} {student.last_name} предложил новую тему: '{proposed_topic}'"
    else:
        message = f"Студент {student.first_name} {student.last_name} выбрал тему '{topic.name}'"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [teacher.email],
        fail_silently=False,
    )

def send_telegram_message(teacher, student, topic, context):
    chat_id = teacher.telegram_chat_id
    #Создание клавиатуры
    approve_button = InlineKeyboardButton("Одобрить", callback_data=f"approve_{student.id}_{topic.id}")
    reject_button = InlineKeyboardButton("Отклонить", callback_data=f"reject_{student.id}_{topic.id}")
    keyboard = InlineKeyboardMarkup([[approve_button, reject_button]])
    #Сообщение
    message_text = f"Заявка от студента {student.first_name} {student.last_name} на тему: {topic.name}"
    #Отправка сообщение через Telegram API
    context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=keyboard)
    return BUTTON_HANDLER


def send_email(to_email, message_text):
    send_mail(
        subject="Статус вашей заявки",
        message=message_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
    )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    data = query.data  # Получаем callback_data

    # Извлекаем ID студента и темы из callback_data
    action, student_id, topic_id = data.split('_')

    if action == 'approve':
        approve_request(student_id, topic_id, query, context)
    elif action == 'reject':
        reject_request(student_id, topic_id, query, context)

def approve_request(student_id, topic_id, query, context):
    # Логика для одобрения заявки
    # Например, обновляем статус в БД
    query.edit_message_text(text="Заявка одобрена.")
    
    # Отправляем сообщение студенту
    student = CustomUser.objects.get(id=student_id)
    context.bot.send_message(chat_id=student.telegram_chat_id, text="Ваша заявка была одобрена.")

    # Отправляем уведомление по email
    send_email(student.email, "Ваша заявка одобрена")

def reject_request(student_id, topic_id, query, context):
    # Логика для отклонения заявки
    # Например, показываем форму для ввода причины отклонения
    query.edit_message_text(text="Заявка отклонена.")
    
    # Отправляем сообщение студенту
    student = CustomUser.objects.get(id=student_id)
    context.bot.send_message(chat_id=student.telegram_chat_id, text="Ваша заявка была отклонена.")

    # Отправляем уведомление по email
    send_email(student.email, "Ваша заявка отклонена")

def confirm_topic_callback(update, context):
    query = update.callback_query
    query.answer()

    # Получаем ID темы
    topic_id = query.data.split('_')[2]
    topic = Topic.objects.get(id=topic_id)
    student = context.user_data['user'].student

    # Создание заявки
    Application.objects.create(student=student, teacher=topic.teacher, topic=topic)
    teacher = CustomUser.objects.get(teacher=topic.teacher)
    # Отправляем уведомление преподавателю на почту и в Telegram
    send_email_to_teacher(teacher, topic, context.user_data['user'])
    send_telegram_message(teacher, student, topic, context)

    query.edit_message_text(f"Заявка на тему '{topic.name}' отправлена на рассмотрение.")

    return ConversationHandler.END

def submit_proposed_topic(update, context):
    proposed_topic = update.message.text
    student = context.user_data['user']
    instructor = Teacher.objects.get(id=context.user_data['teacher_id'])

def stop(update: Update, context):
    update.message.reply_text("Операция завершена.")
    return ConversationHandler.END