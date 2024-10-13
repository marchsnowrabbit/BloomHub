from django.db import models

# Create your models here.

class User(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  
    username = models.CharField(max_length=150, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['email'], name='email_index'),
        ]

    def __str__(self):
        return self.email