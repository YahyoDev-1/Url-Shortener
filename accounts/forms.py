from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

# Barcha input maydonlar uchun umumiy Tailwind klasslari
INPUT_CLASSES = (
    'w-full px-4 py-2.5 rounded-lg bg-slate-800/60 border border-slate-700 '
    'text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 '
    'focus:ring-indigo-500 focus:border-transparent transition'
)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'email@example.com',
        }),
        label='Email',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': 'foydalanuvchi_nomi',
        })
        self.fields['password1'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        })
        self.fields['password2'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        })

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return email


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': 'foydalanuvchi_nomi',
        })
        self.fields['password'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        })
