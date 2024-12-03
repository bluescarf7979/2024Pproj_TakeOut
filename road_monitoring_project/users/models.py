from django.db import models

class User(models.Model):
    user_type = models.IntegerField()
    username = models.CharField(max_length=255)
    email = models.EmailField()
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    preferred_notification_type = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
