from djo .contrib .admindocs import views 
from djo .urls import path ,re_path 

urlpatterns =[
path (
"",
views .BaseAdminDocsView .as_view (template_name ="admin_doc/index.html"),
name ="djodocs-docroot",
),
path (
"bookmarklets/",
views .BookmarkletsView .as_view (),
name ="djodocs-bookmarklets",
),
path (
"tags/",
views .TemplateTagIndexView .as_view (),
name ="djodocs-tags",
),
path (
"filters/",
views .TemplateFilterIndexView .as_view (),
name ="djodocs-filters",
),
path (
"views/",
views .ViewIndexView .as_view (),
name ="djodocs-views-index",
),
path (
"views/<view>/",
views .ViewDetailView .as_view (),
name ="djodocs-views-detail",
),
path (
"models/",
views .ModelIndexView .as_view (),
name ="djodocs-models-index",
),
re_path (
r"^models/(?P<app_label>[^.]+)\.(?P<model_name>[^/]+)/$",
views .ModelDetailView .as_view (),
name ="djodocs-models-detail",
),
path (
"templates/<path:template>/",
views .TemplateDetailView .as_view (),
name ="djodocs-templates",
),
]
