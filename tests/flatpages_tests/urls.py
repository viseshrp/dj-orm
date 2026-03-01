from djo .contrib .flatpages .sitemaps import FlatPageSitemap 
from djo .contrib .sitemaps import views 
from djo .urls import include ,path 

urlpatterns =[
path (
"flatpages/sitemap.xml",
views .sitemap ,
{"sitemaps":{"flatpages":FlatPageSitemap }},
name ="djo.contrib.sitemaps.views.sitemap",
),
path ("flatpage_root/",include ("djo.contrib.flatpages.urls")),
path ("accounts/",include ("djo.contrib.auth.urls")),
]
