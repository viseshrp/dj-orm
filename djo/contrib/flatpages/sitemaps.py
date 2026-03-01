from djo .apps import apps as django_apps 
from djo .contrib .sitemaps import Sitemap 
from djo .core .exceptions import ImproperlyConfigured 


class FlatPageSitemap (Sitemap ):
    def items (self ):
        if not django_apps .is_installed ("djo.contrib.sites"):
            raise ImproperlyConfigured (
            "FlatPageSitemap requires djo.contrib.sites, which isn't installed."
            )
        Site =django_apps .get_model ("sites.Site")
        current_site =Site .objects .get_current ()
        return current_site .flatpage_set .filter (registration_required =False )
