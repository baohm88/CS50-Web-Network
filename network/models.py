from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    following = models.ManyToManyField(
        "self", blank=True, related_name="followers", symmetrical=False
    )

    def __str__(self):
        return str(self.username)

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator')
    body = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, blank=True, null=True, related_name="userlike")

    def __str__(self):
        return (
            f"{self.author} "
            f"({self.date_created:%Y-%m-%d %H:%M}) :"
            f"{self.body}"
        )