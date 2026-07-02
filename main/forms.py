import re

from django import forms
from django.utils import timezone

from .models import ShortURL

# URL yo'nalishlari bilan to'qnashmasligi kerak bo'lgan kodlar
RESERVED_CODES = {
    'admin', 'accounts', 'api', 'stats', 'static', 'media',
    'signup', 'login', 'logout', 'dashboard',
}

CUSTOM_CODE_RE = re.compile(r'^[a-zA-Z0-9_-]{3,15}$')


class ShortURLForm(forms.ModelForm):
    custom_code = forms.CharField(
        required=False,
        max_length=15,
        label='Maxsus kod',
    )
    expires_at = forms.DateTimeField(
        required=False,
        label='Amal qilish muddati',
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%d.%m.%Y %H:%M'],
    )

    class Meta:
        model = ShortURL
        fields = ('original_url',)
        error_messages = {
            'original_url': {
                'required': 'URL manzilni kiriting.',
                'invalid': "To'g'ri URL kiriting (masalan: https://example.com/sahifa).",
                'max_length': 'URL juda uzun (maksimum 2000 belgi).',
            },
        }

    def clean_custom_code(self):
        code = self.cleaned_data.get('custom_code', '').strip()
        if not code:
            return ''
        if not CUSTOM_CODE_RE.match(code):
            raise forms.ValidationError(
                "Maxsus kod 3-15 belgidan iborat bo'lib, faqat harf, raqam, '-' va '_' dan tashkil topishi kerak."
            )
        if code.lower() in RESERVED_CODES:
            raise forms.ValidationError(f"'{code}' kodi band (tizim uchun ajratilgan).")
        if ShortURL.objects.filter(short_code=code).exists():
            raise forms.ValidationError(f"'{code}' kodi allaqachon band. Boshqasini tanlang.")
        return code

    def clean_expires_at(self):
        expires_at = self.cleaned_data.get('expires_at')
        if expires_at and expires_at <= timezone.now():
            raise forms.ValidationError("Muddat kelajakdagi vaqt bo'lishi kerak.")
        return expires_at

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('custom_code'):
            instance.short_code = self.cleaned_data['custom_code']
        instance.expires_at = self.cleaned_data.get('expires_at')
        if commit:
            instance.save()
        return instance
