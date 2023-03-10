from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    request = timezone.now()
    return {
        'year': request.year
    }
