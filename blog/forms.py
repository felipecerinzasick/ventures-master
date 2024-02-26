from django import forms

from .models import Post
from .models import Contact


        
class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'message']
        

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']

        widgets = {
            'content': forms.CharField(label='Content',
                   widget=forms.Textarea(attrs={'class': 'ckeditor'}))
        }
