# core/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, default='light')
    budget = models.FloatField(default=0)
    spending = models.FloatField(default=0)
    color = models.CharField(max_length=7, default='#0d6efd')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense')
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField(default=0)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='expense')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.user.username}"

class SavingsGoal(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal_name = models.CharField(max_length=50)
    target_amount = models.FloatField()
    curr_amount = models.FloatField(default=0.0)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.user.username}"
