try :
    from djo .contrib .gis import admin 
except ImportError :
    from djo .contrib import admin 

    admin .GISModelAdmin =admin .ModelAdmin 
