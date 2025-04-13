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

class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField(default = 0)
    def __str__(self):
        return str(self.id) + ' - ' + self.user.username

