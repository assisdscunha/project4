from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    followers = models.ManyToManyField(
        "self", symmetrical=False, related_name="following"
    )

    def serialize(self):
        return {
            "username": self.username,
            "followers": [f for f in self.followers.all()],
            "following": [f for f in self.following.all()],
        }


class Posts(models.Model):
    user = models.ForeignKey(
        "User", on_delete=models.SET_NULL, null=True, related_name="posts"
    )
    body = models.TextField(blank=False)
    likes = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="comments"
    )

    def get_display_user(self, user):
        return user.username if user and user.is_active else "user removed"

    def serialize_comments(self, comment):
        return {
            "body": comment.body,
            "user": self.get_display_user(comment.user),
            "likes": comment.likes,
            "timestamp": comment.timestamp.strftime("%b %d %Y, %I:%M %p"),
        }

    def serialize(self):
        return {
            "user": self.get_display_user(self.user),
            "body": self.body,
            "likes": self.likes,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "comments": [
                self.serialize_comments(comment)
                for comment in self.comments.all()
            ],
        }
