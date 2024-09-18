from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_student = models.BooleanField(default=False)
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Telegram Chat ID")

class Course(models.Model):
    year = models.CharField(max_length=100)
    op = models.CharField(max_length=100)

class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, related_name='teachers')
    max_students = models.IntegerField(default=0)

class Topic(models.Model):
    name = models.CharField(max_length=200)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE,  null=True)
    is_available = models.BooleanField(default=True)

class Application(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)


    