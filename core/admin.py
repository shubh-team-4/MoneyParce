from django.contrib import admin

from .models import Transaction, UserProfile, Category


admin.site.register(UserProfile)
admin.site.register(Transaction)
admin.site.register(Category)
# Register your models here.
