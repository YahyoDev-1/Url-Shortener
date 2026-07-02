from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Click, ShortURL
from .utils import parse_user_agent


class ShortURLModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')

    def test_short_code_auto_generated_and_unique(self):
        url1 = ShortURL.objects.create(owner=self.user, original_url='https://example.com/1')
        url2 = ShortURL.objects.create(owner=self.user, original_url='https://example.com/2')
        self.assertTrue(url1.short_code)
        self.assertNotEqual(url1.short_code, url2.short_code)

    def test_get_short_url(self):
        url = ShortURL.objects.create(owner=self.user, original_url='https://example.com')
        self.assertEqual(url.get_short_url(), f'/{url.short_code}/')


class ShortenApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')

    def test_shorten_requires_login(self):
        response = self.client.post(reverse('main:shorten'), {'original_url': 'https://example.com'})
        self.assertEqual(response.status_code, 302)  # login sahifasiga redirect

    def test_shorten_creates_url(self):
        self.client.login(username='egasi', password='Parol-123')
        response = self.client.post(reverse('main:shorten'), {'original_url': 'https://example.com/sahifa'})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(ShortURL.objects.filter(short_code=data['url']['short_code'], owner=self.user).exists())

    def test_shorten_rejects_invalid_url(self):
        self.client.login(username='egasi', password='Parol-123')
        response = self.client.post(reverse('main:shorten'), {'original_url': 'bu url emas'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertEqual(ShortURL.objects.count(), 0)


class RedirectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')
        self.url = ShortURL.objects.create(owner=self.user, original_url='https://example.com/manzil')

    def test_redirect_works_and_increments_clicks(self):
        response = self.client.get(f'/{self.url.short_code}/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://example.com/manzil')
        self.url.refresh_from_db()
        self.assertEqual(self.url.clicks, 1)

    def test_unknown_code_returns_404(self):
        response = self.client.get('/yoqkod123/')
        self.assertEqual(response.status_code, 404)

    def test_admin_not_shadowed_by_redirect(self):
        # '<slug>/' pattern admin sahifasini yutib yubormasligi kerak
        response = self.client.get('/admin/', follow=False)
        self.assertIn(response.status_code, (301, 302))  # admin login'ga redirect


class DeleteUrlTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')
        self.other = User.objects.create_user('begona', 'begona@example.com', 'Parol-123')
        self.url = ShortURL.objects.create(owner=self.owner, original_url='https://example.com')

    def test_owner_can_delete(self):
        self.client.login(username='egasi', password='Parol-123')
        response = self.client.post(reverse('main:delete_url', args=[self.url.short_code]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ShortURL.objects.filter(pk=self.url.pk).exists())

    def test_other_user_cannot_delete(self):
        self.client.login(username='begona', password='Parol-123')
        response = self.client.post(reverse('main:delete_url', args=[self.url.short_code]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ShortURL.objects.filter(pk=self.url.pk).exists())


class CustomCodeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')
        self.client.login(username='egasi', password='Parol-123')

    def _shorten(self, **extra):
        return self.client.post(reverse('main:shorten'), {'original_url': 'https://example.com', **extra})

    def test_custom_code_accepted(self):
        response = self._shorten(custom_code='mening-kodim')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['url']['short_code'], 'mening-kodim')

    def test_custom_code_taken_rejected(self):
        ShortURL.objects.create(owner=self.user, original_url='https://example.com', short_code='band-kod')
        response = self._shorten(custom_code='band-kod')
        self.assertEqual(response.status_code, 400)
        self.assertIn('band', response.json()['errors'][0])

    def test_reserved_code_rejected(self):
        response = self._shorten(custom_code='admin')
        self.assertEqual(response.status_code, 400)

    def test_invalid_chars_rejected(self):
        response = self._shorten(custom_code='ab')  # juda qisqa
        self.assertEqual(response.status_code, 400)
        response = self._shorten(custom_code='kod bilan probel')
        self.assertEqual(response.status_code, 400)


class ExpirationAndToggleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')
        self.other = User.objects.create_user('begona', 'begona@example.com', 'Parol-123')
        self.url = ShortURL.objects.create(owner=self.user, original_url='https://example.com')

    def test_expired_link_returns_410_and_no_click(self):
        self.url.expires_at = timezone.now() - timedelta(hours=1)
        self.url.save()
        response = self.client.get(f'/{self.url.short_code}/')
        self.assertEqual(response.status_code, 410)
        self.assertTemplateUsed(response, 'main/link_gone.html')
        self.assertEqual(Click.objects.count(), 0)
        self.url.refresh_from_db()
        self.assertEqual(self.url.clicks, 0)

    def test_inactive_link_returns_410(self):
        self.url.is_active = False
        self.url.save()
        response = self.client.get(f'/{self.url.short_code}/')
        self.assertEqual(response.status_code, 410)

    def test_active_link_with_future_expiry_works(self):
        self.url.expires_at = timezone.now() + timedelta(days=7)
        self.url.save()
        response = self.client.get(f'/{self.url.short_code}/')
        self.assertEqual(response.status_code, 302)

    def test_past_expiry_rejected_on_create(self):
        self.client.login(username='egasi', password='Parol-123')
        response = self.client.post(reverse('main:shorten'), {
            'original_url': 'https://example.com/yangi',
            'expires_at': '2020-01-01T00:00',
        })
        self.assertEqual(response.status_code, 400)

    def test_toggle_flips_state(self):
        self.client.login(username='egasi', password='Parol-123')
        response = self.client.post(reverse('main:toggle_url', args=[self.url.short_code]))
        data = response.json()
        self.assertFalse(data['is_active'])
        self.assertEqual(data['status'], 'inactive')
        self.url.refresh_from_db()
        self.assertFalse(self.url.is_active)

        response = self.client.post(reverse('main:toggle_url', args=[self.url.short_code]))
        self.assertTrue(response.json()['is_active'])

    def test_toggle_owner_only(self):
        self.client.login(username='begona', password='Parol-123')
        response = self.client.post(reverse('main:toggle_url', args=[self.url.short_code]))
        self.assertEqual(response.status_code, 404)


class QRCodeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')
        self.other = User.objects.create_user('begona', 'begona@example.com', 'Parol-123')
        self.url = ShortURL.objects.create(owner=self.user, original_url='https://example.com')

    def test_qr_returns_png(self):
        self.client.login(username='egasi', password='Parol-123')
        response = self.client.get(reverse('main:qr', args=[self.url.short_code]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(response.content.startswith(b'\x89PNG'))

    def test_qr_owner_only(self):
        self.client.login(username='begona', password='Parol-123')
        response = self.client.get(reverse('main:qr', args=[self.url.short_code]))
        self.assertEqual(response.status_code, 404)


class UserAgentParserTests(TestCase):
    def test_chrome_desktop(self):
        browser, device = parse_user_agent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
        )
        self.assertEqual((browser, device), ('Chrome', 'Kompyuter'))

    def test_safari_iphone(self):
        browser, device = parse_user_agent(
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        )
        self.assertEqual((browser, device), ('Safari', 'Mobil'))

    def test_bot(self):
        browser, device = parse_user_agent('python-requests/2.32')
        self.assertEqual(device, 'Bot')

    def test_empty(self):
        browser, device = parse_user_agent('')
        self.assertEqual((browser, device), ('Boshqa', 'Kompyuter'))


class ClickAnalyticsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')
        self.other = User.objects.create_user('begona', 'begona@example.com', 'Parol-123')
        self.url = ShortURL.objects.create(owner=self.user, original_url='https://example.com')

    def test_redirect_creates_click_record(self):
        self.client.get(
            f'/{self.url.short_code}/',
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0) Chrome/126.0 Safari/537.36',
            HTTP_REFERER='https://t.me/kanal',
        )
        click = Click.objects.get(short_url=self.url)
        self.assertEqual(click.browser, 'Chrome')
        self.assertEqual(click.device, 'Kompyuter')
        self.assertEqual(click.referrer, 'https://t.me/kanal')

    def test_stats_api_returns_data(self):
        self.client.get(f'/{self.url.short_code}/', HTTP_USER_AGENT='Chrome/126.0 Safari/537.36')
        self.client.login(username='egasi', password='Parol-123')
        response = self.client.get(reverse('main:stats_api', args=[self.url.short_code]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_clicks'], 1)
        self.assertEqual(data['today_clicks'], 1)
        self.assertEqual(len(data['daily']['labels']), 30)
        self.assertEqual(sum(data['daily']['values']), 1)
        self.assertEqual(len(data['recent']), 1)

    def test_stats_page_owner_only(self):
        self.client.login(username='begona', password='Parol-123')
        page = self.client.get(reverse('main:stats', args=[self.url.short_code]))
        api = self.client.get(reverse('main:stats_api', args=[self.url.short_code]))
        self.assertEqual(page.status_code, 404)
        self.assertEqual(api.status_code, 404)

    def test_deleting_url_removes_clicks(self):
        self.client.get(f'/{self.url.short_code}/')
        self.url.delete()
        self.assertEqual(Click.objects.count(), 0)


class DashboardListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('egasi', 'ega@example.com', 'Parol-123')
        self.other = User.objects.create_user('begona', 'begona@example.com', 'Parol-123')
        ShortURL.objects.create(owner=self.user, original_url='https://example.com/meniki')
        ShortURL.objects.create(owner=self.other, original_url='https://example.com/begonaniki')

    def test_dashboard_shows_only_own_urls(self):
        self.client.login(username='egasi', password='Parol-123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertContains(response, 'https://example.com/meniki')
        self.assertNotContains(response, 'https://example.com/begonaniki')
        self.assertEqual(response.context['total_urls'], 1)

    def test_dashboard_today_clicks_counts_only_own(self):
        my_url = ShortURL.objects.get(original_url='https://example.com/meniki')
        other_url = ShortURL.objects.get(original_url='https://example.com/begonaniki')
        self.client.get(f'/{my_url.short_code}/')
        self.client.get(f'/{other_url.short_code}/')

        self.client.login(username='egasi', password='Parol-123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.context['today_clicks'], 1)
