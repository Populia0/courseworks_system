from django.contrib import admin

from django.contrib import admin
from .models import CustomUser, Teacher, Student, Course, Topic, Application

admin.site.register(CustomUser)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Topic)
admin.site.register(Application)