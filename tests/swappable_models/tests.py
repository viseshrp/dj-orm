from djrm.contrib.contenttypes.models import ContentType
from djrm.core import management
from djrm.test import TestCase, override_settings

from .models import Article


class SwappableModelTests(TestCase):
    # Limit memory usage when calling 'migrate'.
    available_apps = [
        "swappable_models",
        "djrm.contrib.contenttypes",
    ]

    @override_settings(TEST_ARTICLE_MODEL="swappable_models.AlternateArticle")
    def test_generated_data(self):
        "Content types are not created for a swapped model."

        # Delete all content types for the app.
        ContentType.objects.filter(app_label="swappable_models").delete()

        # Re-run migrate. This rebuilds content types.
        management.call_command("migrate", interactive=False, verbosity=0)

        # A content type exists for the replacement, but not the swapped model.
        apps_models = [(ct.app_label, ct.model) for ct in ContentType.objects.all()]
        self.assertIn(("swappable_models", "alternatearticle"), apps_models)
        self.assertNotIn(("swappable_models", "article"), apps_models)

    @override_settings(TEST_ARTICLE_MODEL="swappable_models.article")
    def test_case_insensitive(self):
        "Model names are case insensitive. Model swapping honors this."
        Article.objects.all()
        self.assertIsNone(Article._meta.swapped)
