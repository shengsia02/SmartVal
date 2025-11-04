from django.db import models

class Agent(models.Model):
    """房屋中介"""
    name = models.CharField(max_length=100, verbose_name='房屋中介名稱')
    city = models.CharField(max_length=50, verbose_name='分行所在縣市')
    town = models.CharField(max_length=50, verbose_name='分行所在行政區')

    class Meta:
        verbose_name = '房屋中介'
        verbose_name_plural = '房屋中介'

    def __str__(self):
        return self.name
