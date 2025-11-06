from django.db import models

class Agent(models.Model):
    """房屋仲介(指特定人員)"""
    name = models.CharField(max_length=100, verbose_name='仲介姓名')
    phone = models.CharField(max_length=20, verbose_name='聯絡電話', blank=True)
    email = models.EmailField(max_length=100, verbose_name='電子郵件', blank=True)
    company = models.CharField(max_length=100, verbose_name='隸屬公司', blank=True, help_text="例如：oo房屋")
    branch = models.CharField(max_length=100, verbose_name='分行名稱', blank=True, help_text="例如：三峽店")
    city = models.CharField(max_length=50, verbose_name='分行所在縣市')
    town = models.CharField(max_length=50, verbose_name='分行所在行政區')

    class Meta:
        verbose_name = '房屋仲介'
        verbose_name_plural = '房屋仲介'

    def __str__(self):
        return self.name
