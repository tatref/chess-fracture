from enum import Enum

from django.db import models

# Create your models here.



class Game(models.Model):
    site = models.CharField(max_length=10)
    gameid = models.CharField(max_length=15)
    pgn = models.TextField(blank=True)
    lastmodified = models.DateTimeField(auto_now=True)
    status =  models.PositiveSmallIntegerField()  # new, downloaded, simulating, done, failed

    class Meta:
        unique_together = (('site', 'gameid'),)

    def __str__(self):
        return self.site + '/' + self.gameid


    


