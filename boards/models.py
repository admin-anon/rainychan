from io import BytesIO
from PIL import Image

from django.core.files import File
from django.db import models
from django.contrib.auth.models import User

class Board(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField()

class Post(models.Model):
    contents = models.TextField()
    attachment = models.ImageField(null=True, upload_to='uploads/attachments/%Y/%m/%d/')
    thumbnail = models.ImageField(null=True, upload_to='uploads/thumbnails/%Y/%m/%d/')
    posted = models.DateTimeField(auto_now_add=True)
    tripcode = models.CharField(null=True, max_length=40)
    post_number = models.IntegerField()
    from_ip = models.GenericIPAddressField()
    password_hash = models.CharField(blank=True, max_length=128)
    banned_for = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        posts = list(Topic.objects.filter(on_board=self.on_board)) + list(Reply.objects.filter(on_board=self.on_board))
        if len(posts) == 0:
            self.post_number = 1
        else:
            self.post_number = max([post.post_number for post in posts]) + 1

        if self.attachment:
            thumbnail = Image.open(self.attachment).convert('RGB')
            thumbnail.thumbnail((200, 200))

            thumb_io = BytesIO()
            thumbnail.save(thumb_io, format='JPEG', quality=85)
            self.thumbnail = File(thumb_io, name=self.attachment.name + '.thumbnail.jpeg')
        
        super().save(*args, **kwargs)
    
    def save_mod(self, *args, **kwargs):
        super().save(*args, **kwargs)

class Topic(Post):
    subject = models.CharField(null=True, max_length=100)
    by_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='topics')
    on_board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='topics')

class Reply(Post):
    on_topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='replies')
    by_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='replies')
    on_board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='replies')

class BannedIP(models.Model):
    ip = models.GenericIPAddressField()