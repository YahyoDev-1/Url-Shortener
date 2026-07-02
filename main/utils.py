"""Yordamchi funksiyalar: User-Agent tahlili va IP aniqlash."""

BOT_KEYWORDS = ('bot', 'crawler', 'spider', 'curl', 'wget', 'python-requests', 'httpclient')


def parse_user_agent(user_agent: str) -> tuple[str, str]:
    """User-Agent satridan (brauzer, qurilma) juftligini aniqlaydi.

    Tashqi kutubxonasiz, oddiy kalit so'z tahlili — portfolio miqyosi uchun yetarli.
    """
    ua = (user_agent or '').lower()

    # Qurilma turi
    if any(bot in ua for bot in BOT_KEYWORDS):
        device = 'Bot'
    elif 'ipad' in ua or 'tablet' in ua:
        device = 'Planshet'
    elif 'mobi' in ua or 'android' in ua or 'iphone' in ua:
        device = 'Mobil'
    else:
        device = 'Kompyuter'

    # Brauzer (tartib muhim: Edge/Opera UA'sida "chrome" ham bor)
    if 'edg' in ua:
        browser = 'Edge'
    elif 'opr' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'firefox' in ua or 'fxios' in ua:
        browser = 'Firefox'
    elif 'chrome' in ua or 'crios' in ua:
        browser = 'Chrome'
    elif 'safari' in ua:
        browser = 'Safari'
    else:
        browser = 'Boshqa'

    return browser, device


def get_client_ip(request) -> str | None:
    """Proksi ortida ham ishlaydigan mijoz IP manzili."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
