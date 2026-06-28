from django.conf import settings


def public_site(request):
    return {
        'PUBLIC_SITE_ONLY': getattr(settings, 'PUBLIC_SITE_ONLY', False),
    }
