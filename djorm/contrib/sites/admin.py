from djorm.contrib import admin
from djorm.contrib.sites.models import Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("domain", "name")
    search_fields = ("domain", "name")
