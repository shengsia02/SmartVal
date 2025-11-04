from django.db import models

class Buyer(models.Model):
    """買家"""
    name = models.CharField(max_length=100, verbose_name='姓名')
    occup = models.TextField(blank=True, verbose_name='職業')
    birth_date = models.DateField(null=True, blank=True, verbose_name='出生日期')
    nationality = models.CharField(max_length=50, blank=True, verbose_name='國籍')

    class Meta:
        verbose_name = '買家'
        verbose_name_plural = '買家'

    def __str__(self):
        return self.name
