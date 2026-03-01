import os 

AUTH_MIDDLEWARE =[
"djo.contrib.sessions.middleware.SessionMiddleware",
"djo.contrib.auth.middleware.AuthenticationMiddleware",
]

AUTH_TEMPLATES =[
{
"BACKEND":"djo.template.backends.django.DjangoTemplates",
"DIRS":[os .path .join (os .path .dirname (__file__ ),"templates")],
"APP_DIRS":True ,
"OPTIONS":{
"context_processors":[
"djo.template.context_processors.request",
"djo.contrib.auth.context_processors.auth",
"djo.contrib.messages.context_processors.messages",
],
},
}
]
