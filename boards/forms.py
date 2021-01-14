from django import forms
from .models import Topic
from captcha.fields import CaptchaField

class TopicForm(forms.Form):
    topicform_identifier = forms.BooleanField(widget=forms.HiddenInput(), initial=True)
    subject = forms.CharField(required=False, max_length=100)
    tripcode = forms.CharField(required=False, max_length=40)
    contents = forms.CharField(widget=forms.Textarea(attrs={'class': 'post-form'}))
    attachment = forms.ImageField(required=False)
    password = forms.CharField(max_length=25, widget=forms.TextInput(attrs={'class': 'password-input'}))
    captcha_field = CaptchaField()

class ReplyForm(forms.Form):
    replyform_identifier = forms.BooleanField(widget=forms.HiddenInput(), initial=True)
    to_topic = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': 'topic-number-input'}))
    tripcode = forms.CharField(required=False, max_length=40)
    contents = forms.CharField(widget=forms.Textarea(attrs={'class': 'post-form'}))
    attachment = forms.ImageField(required=False)
    password = forms.CharField(max_length=25, widget=forms.TextInput(attrs={'class': 'password-input'}))
    captcha_field = CaptchaField()
    post_number = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': 'post_number'}))

class DeletionForm(forms.Form):
    deleteform_identifier = forms.BooleanField(widget=forms.HiddenInput(), initial=True)
    password = forms.CharField(max_length=25, widget=forms.TextInput(attrs={'class': 'deletion-input'}))
    post_number = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': 'deletion-form-secret'}))
    captcha_field = CaptchaField()

class BanForm(forms.Form):
    banform_identifier = forms.BooleanField(widget=forms.HiddenInput(), initial=True)
    captcha_field = CaptchaField()
    post_number = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': 'ban-form'}))