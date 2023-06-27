from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from .manager import UserManager

from django.contrib.auth.signals import user_logged_in, user_logged_out 
import datetime

class Interests(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["-name"]




class User(AbstractUser):
    username = None
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=100 , unique=True)
    gender = models.CharField(max_length=10 , choices=(("MALE", "MALE") , ("FEMAIL", "FEMALE"))) 
    country = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    interests  = models.ManyToManyField(to=Interests)
    is_online = models.BooleanField(default=False)
    inside_room = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def name(self):
        return f'{self.first_name} {self.last_name}'

    def get_interests(self):
        interests = [interest.name for interest in self.interests.all()]
        print(interests)
        return interests


    def __str__(self):
        return self.email













