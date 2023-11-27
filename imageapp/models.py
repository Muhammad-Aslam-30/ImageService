from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

def validate_url(value):
    url_validator = URLValidator()
    try:
        url_validator(value)
    except ValidationError as e:
        raise ValidationError('Enter a valid URL.')

# Create your models here.
class Images(models.Model):
    url = models.URLField(primary_key=True, validators=[validate_url])
    imagename = models.CharField(max_length=255)