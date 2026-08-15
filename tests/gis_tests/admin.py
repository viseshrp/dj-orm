try:
    from djorm.contrib.gis import admin
except ImportError:
    from djorm.contrib import admin

    admin.GISModelAdmin = admin.ModelAdmin
