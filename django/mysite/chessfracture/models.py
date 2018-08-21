from enum import Enum

from django.db import models

# Create your models here.



class Game(models.Model):
    site = models.CharField(max_length=20)
    gameid = models.CharField(max_length=20)

    status =  models.SmallIntegerField()    # done(0), new(1), pgn_downloaded(2), simulating(3), failed(-1)
    errormessage = models.TextField(default=None, blank=True, null=True)

    submitdate = models.DateTimeField(auto_now_add=True)
    lastdl = models.DateTimeField(default=None, blank=True, null=True)

    pgn = models.TextField(default=None, blank=True, null=True)
    blend = models.BinaryField()

    class Meta:
        unique_together = (('site', 'gameid'),)

    def __str__(self):
        return self.site + '/' + self.gameid


    


