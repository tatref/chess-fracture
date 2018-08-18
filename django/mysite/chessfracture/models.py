from enum import Enum

from django.db import models

# Create your models here.



class Game(models.Model):
    site = models.CharField(max_length=20)
    gameid = models.CharField(max_length=20)
    pgn = models.TextField(blank=True)
    lastmodified = models.DateTimeField(auto_now=True)
    status =  models.SmallIntegerField()  # new(0), downloaded(1), simulating(2), done(3), failed(-1)
    errormessage = models.TextField(blank=True)

    class Meta:
        unique_together = (('site', 'gameid'),)

    def __str__(self):
        return self.site + '/' + self.gameid


    


