from django.db import models
from users.models import User
from road_info.models import RoadInfo

class Post(models.Model):
    post_type = models.IntegerField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    info = models.ForeignKey(RoadInfo, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
