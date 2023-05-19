from django import forms
from .models import Post, NewsletterUser


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']

        widgets = {
            'content': forms.CharField(label='Content',
                   widget=forms.Textarea(attrs={'class': 'ckeditor'}))
        }


class NewsletterUserForm(forms.ModelForm):
    class Meta:
        model = NewsletterUser
        fields = ['email']
