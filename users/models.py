from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(AbstractUser):
    email = models.EmailField(unique=True)
    secret_question = models.CharField(max_length=255, blank=True, null=True)
    secret_answer = models.CharField(max_length=255, blank=True, null=True)

    def set_secret_answer(self, raw_answer):
        if raw_answer is None or raw_answer == "":
            self.secret_answer = None
        else:
            self.secret_answer = make_password(raw_answer)

    def check_secret_answer(self, raw_answer):
        if not self.secret_answer:
            return False
        return check_password(raw_answer, self.secret_answer)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)