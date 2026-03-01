from djo .core import checks 
from djo .db import models 


class ModelRaisingMessages (models .Model ):
    @classmethod 
    def check (self ,**kwargs ):
        return [checks .Warning ("A warning")]
