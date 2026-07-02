import io
from collections import Counter
from datetime import timedelta

import qrcode
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ShortURLForm
from .models import Click, ShortURL
from .utils import get_client_ip, parse_user_agent


def home_view(request):
    return render(request, 'main/home.html')


def redirect_view(request, short_code):
    """Qisqa kod bo'yicha asl URL'ga yo'naltiradi va bosishni qayd etadi."""
    short_url = get_object_or_404(ShortURL, short_code=short_code)

    # To'xtatilgan yoki muddati tugagan havola — 410 Gone
    if not short_url.is_available:
        return render(request, 'main/link_gone.html', {'short_url': short_url}, status=410)

    # F() — poyga holatisiz (race condition) atomar oshirish
    ShortURL.objects.filter(pk=short_url.pk).update(clicks=F('clicks') + 1)

    # Analytics uchun batafsil yozuv
    browser, device = parse_user_agent(request.META.get('HTTP_USER_AGENT', ''))
    Click.objects.create(
        short_url=short_url,
        referrer=request.META.get('HTTP_REFERER', '')[:2000],
        ip_address=get_client_ip(request),
        browser=browser,
        device=device,
    )

    return redirect(short_url.original_url)


@login_required
@require_POST
def shorten_view(request):
    """AJAX: yangi qisqa havola yaratadi va JSON qaytaradi."""
    form = ShortURLForm(request.POST)
    if not form.is_valid():
        errors = [error for field_errors in form.errors.values() for error in field_errors]
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    short_url = form.save(commit=False)
    short_url.owner = request.user
    short_url.save()

    return JsonResponse({
        'success': True,
        'url': _serialize(short_url, request),
    }, status=201)


@login_required
@require_POST
def delete_url_view(request, short_code):
    """AJAX: foydalanuvchining o'z havolasini o'chiradi."""
    short_url = get_object_or_404(ShortURL, short_code=short_code, owner=request.user)
    short_url.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def toggle_url_view(request, short_code):
    """AJAX: havolani faollashtirish/to'xtatish."""
    short_url = get_object_or_404(ShortURL, short_code=short_code, owner=request.user)
    short_url.is_active = not short_url.is_active
    short_url.save(update_fields=['is_active'])
    return JsonResponse({
        'success': True,
        'is_active': short_url.is_active,
        'status': short_url.status,
    })


@login_required
def qr_view(request, short_code):
    """Qisqa havola uchun QR-kod (PNG rasm)."""
    short_url = get_object_or_404(ShortURL, short_code=short_code, owner=request.user)
    img = qrcode.make(short_url.get_short_url(request), box_size=10, border=2)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="qr-{short_url.short_code}.png"'
    return response


@login_required
def stats_view(request, short_code):
    """Bitta havola bo'yicha statistika sahifasi (faqat egasi uchun)."""
    short_url = get_object_or_404(ShortURL, short_code=short_code, owner=request.user)
    return render(request, 'main/stats.html', {'short_url': short_url})


@login_required
def stats_api_view(request, short_code):
    """AJAX: havola statistikasi JSON ko'rinishida (Chart.js uchun)."""
    short_url = get_object_or_404(ShortURL, short_code=short_code, owner=request.user)

    now = timezone.localtime()
    today = now.date()
    start_date = today - timedelta(days=29)

    clicks = list(
        short_url.click_events.filter(created_at__gte=now - timedelta(days=30))
        .values('created_at', 'browser', 'device')
    )

    # Kunlik bosishlar (oxirgi 30 kun) — Python tomonda guruhlash,
    # MongoDB backend'ga murakkab aggregation yuklamaslik uchun
    daily = Counter(timezone.localtime(c['created_at']).date() for c in clicks)
    labels, values = [], []
    for i in range(30):
        day = start_date + timedelta(days=i)
        labels.append(day.strftime('%d.%m'))
        values.append(daily.get(day, 0))

    browsers = Counter(c['browser'] for c in clicks)
    devices = Counter(c['device'] for c in clicks)

    recent = [
        {
            'time': timezone.localtime(c.created_at).strftime('%d.%m.%Y %H:%M'),
            'referrer': c.referrer or 'To\'g\'ridan-to\'g\'ri',
            'browser': c.browser,
            'device': c.device,
        }
        for c in short_url.click_events.all()[:10]
    ]

    return JsonResponse({
        'success': True,
        'total_clicks': short_url.clicks,
        'today_clicks': daily.get(today, 0),
        'daily': {'labels': labels, 'values': values},
        'browsers': dict(browsers),
        'devices': dict(devices),
        'recent': recent,
    })


def _serialize(short_url, request):
    return {
        'short_code': short_url.short_code,
        'short_url': short_url.get_short_url(request),
        'original_url': short_url.original_url,
        'clicks': short_url.clicks,
        'is_active': short_url.is_active,
        'status': short_url.status,
        'expires_at': (
            timezone.localtime(short_url.expires_at).strftime('%d.%m.%Y %H:%M')
            if short_url.expires_at else None
        ),
        'created_at': short_url.created_at.strftime('%d.%m.%Y %H:%M'),
    }
