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

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        topics = Topic.objects.order_by('-posted').filter(on_board=self.on_board)
        replies = Reply.objects.order_by('-posted').filter(on_board=self.on_board)

        if topics.count() == 0:
            self.post_number = 1
        elif replies.count() == 0:
            self.post_number = topics[0].post_number + 1
        else:
            if topics[0].post_number > replies[0].post_number:
                self.post_number = topics[0].post_number + 1
            elif topics[0].post_number == replies[0].post_number:
                replies[0].delete()
                self.post_number = topics[0].post_number + 1
            else:
                self.post_number = replies[0].post_number + 1

        self.post_number = Topic.objects.filter(on_board=self.on_board).count() + Reply.objects.filter(on_board=self.on_board).count()

        if self.attachment:
            image = Image.open(self.attachment).convert('RGB')
            width, height = image.size
            new_width = min(width, 200)
            new_height = int(height * new_width / width)
            thumbnail = image.resize((new_width, new_height), Image.ANTIALIAS)

            thumb_io = BytesIO()
            thumbnail.save(thumb_io, format='JPEG', quality=85)
            self.thumbnail = File(thumb_io, name=self.attachment.name + '.thumbnail.jpeg')
        
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