web: python manage.py migrate --fake-initial --noinput && python  manage.py  collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT

