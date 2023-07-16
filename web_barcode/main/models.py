from django.db import models


class AddPostFile(models.Model):
    media = models.FileField(upload_to="media", null=True, blank=True)
    cond_for_search = models.BooleanField()
    min_watches = models.IntegerField()
    max_ctr = models.FloatField()
 