import os

FLATPAGES_TEMPLATES = [
    {
        "BACKEND": 'djorm.template.backends.django.DjangoTemplates',
        "DIRS": [os.path.join(os.path.dirname(__file__), "templates")],
        "OPTIONS": {
            "context_processors": ('djorm.contrib.auth.context_processors.auth',),
        },
    }
]
