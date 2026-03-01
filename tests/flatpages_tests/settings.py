import os 

FLATPAGES_TEMPLATES =[
{
"BACKEND":"djo.template.backends.django.DjangoTemplates",
"DIRS":[os .path .join (os .path .dirname (__file__ ),"templates")],
"OPTIONS":{
"context_processors":("djo.contrib.auth.context_processors.auth",),
},
}
]
