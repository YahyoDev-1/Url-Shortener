from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from main.models import Click, ShortURL

from .forms import LoginForm, SignUpForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Xush kelibsiz, {user.username}! Ro'yxatdan muvaffaqiyatli o'tdingiz.")
            return redirect('accounts:dashboard')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, f"Xush kelibsiz, {form.get_user().username}!")
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or 'accounts:dashboard')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan chiqdingiz.")
    return redirect('main:home')


@login_required
def dashboard_view(request):
    urls = ShortURL.objects.filter(owner=request.user)
    total_clicks = urls.aggregate(total=Sum('clicks'))['total'] or 0
    top_url = urls.order_by('-clicks').first()

    # Bugungi bosishlar (mahalliy vaqt bo'yicha kun boshidan)
    day_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    url_ids = list(urls.values_list('pk', flat=True))
    today_clicks = Click.objects.filter(short_url_id__in=url_ids, created_at__gte=day_start).count()

    context = {
        'urls': urls,
        'total_urls': urls.count(),
        'total_clicks': total_clicks,
        'today_clicks': today_clicks,
        'top_clicks': top_url.clicks if top_url else 0,
    }
    return render(request, 'accounts/dashboard.html', context)
