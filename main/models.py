import shortuuid
from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_short_code(length: int = 7) -> str:
    """O'qish oson bo'lgan tasodifiy qisqa kod yaratadi (masalan: 'Xk3fT9a')."""
    return shortuuid.ShortUUID().random(length=length)


class ShortURL(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='short_urls',
        verbose_name='Egasi',
    )
    original_url = models.URLField('Asl URL', max_length=2000)
    short_code = models.SlugField('Qisqa kod', max_length=15, unique=True, blank=True)
    clicks = models.PositiveIntegerField('Bosishlar', default=0)
    is_active = models.BooleanField('Faol', default=True)
    expires_at = models.DateTimeField('Amal qilish muddati', null=True, blank=True)
    created_at = models.DateTimeField('Yaratilgan vaqti', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Qisqa havola'
        verbose_name_plural = 'Qisqa havolalar'

    def __str__(self):
        return f'{self.short_code} -> {self.original_url[:50]}'

    def save(self, *args, **kwargs):
        if not self.short_code:
            # Kod band bo'lsa (juda kam ehtimol), yangisini generatsiya qilamiz
            code = generate_short_code()
            while ShortURL.objects.filter(short_code=code).exists():
                code = generate_short_code()
            self.short_code = code
        super().save(*args, **kwargs)

    def get_short_url(self, request=None):
        """To'liq qisqa havolani qaytaradi (http://.../<code>/)."""
        path = f'/{self.short_code}/'
        if request is not None:
            return request.build_absolute_uri(path)
        return path

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and timezone.now() > self.expires_at

    @property
    def status(self) -> str:
        """'active' | 'inactive' | 'expired' — UI'da badge uchun."""
        if self.is_expired:
            return 'expired'
        return 'active' if self.is_active else 'inactive'

    @property
    def is_available(self) -> bool:
        """Redirect ishlashi mumkinmi?"""
        return self.is_active and not self.is_expired


class Click(models.Model):
    """Har bir o'tish (redirect) haqidagi yozuv — analytics uchun."""

    short_url = models.ForeignKey(
        ShortURL,
        on_delete=models.CASCADE,
        related_name='click_events',
        verbose_name='Havola',
    )
    created_at = models.DateTimeField('Vaqti', auto_now_add=True, db_index=True)
    referrer = models.CharField('Manba (referrer)', max_length=2000, blank=True)
    ip_address = models.GenericIPAddressField('IP manzil', null=True, blank=True)
    browser = models.CharField('Brauzer', max_length=32, default='Boshqa')
    device = models.CharField('Qurilma', max_length=32, default='Kompyuter')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bosish'
        verbose_name_plural = 'Bosishlar'

    def __str__(self):
        return f'{self.short_url.short_code} — {self.created_at:%d.%m.%Y %H:%M}'
