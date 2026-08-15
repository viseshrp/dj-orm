import os

AUTH_MIDDLEWARE = [
    'djorm.contrib.sessions.middleware.SessionMiddleware',
    'djorm.contrib.auth.middleware.AuthenticationMiddleware',
]

AUTH_TEMPLATES = [
    {
        "BACKEND": 'djorm.template.backends.django.DjangoTemplates',
        "DIRS": [os.path.join(os.path.dirname(__file__), "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                'djorm.template.context_processors.request',
                'djorm.contrib.auth.context_processors.auth',
                'djorm.contrib.messages.context_processors.messages',
            ],
        },
    }
]
