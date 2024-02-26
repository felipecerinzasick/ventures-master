from django import forms

from .models import Post
from .models import Contact

from .models import BitcoinWallet  # Ensure this import is correct


class BitcoinWalletForm(forms.ModelForm):
    class Meta:
        model = BitcoinWallet
        fields = ['wallet_address']

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
