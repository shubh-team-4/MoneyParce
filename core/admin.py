from django.contrib import admin

from .models import Transaction, UserProfile


admin.site.register(UserProfile)
admin.site.register(Transaction)
# Register your models here.
