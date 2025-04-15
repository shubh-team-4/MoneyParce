from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, default='light')
    budget = models.FloatField(default = 0)
    spending = models.FloatField(default = 0)

    def __str__(self):
        return self.user.username

# New model for expenditure categories (User Story #11)
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# changed the transaction model to support income/expense and categorization (user Stories 8, 9, 10)
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
