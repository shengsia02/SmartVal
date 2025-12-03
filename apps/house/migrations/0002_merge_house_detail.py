# Generated migration for merging HouseDetail into House

from django.db import migrations, models


def merge_house_detail_to_house(apps, schema_editor):
    """
    將 HouseDetail 的數據合併到 House
    """
    House = apps.get_model('house', 'House')
    HouseDetail = apps.get_model('house', 'HouseDetail')
    
    print("開始合併 HouseDetail 數據到 House...")
    
    count = 0
    for detail in HouseDetail.objects.all():
        house = detail.house
        
        # 將 HouseDetail 的欄位複製到 House
        house.city = detail.city
        house.town = detail.town
        house.house_age = detail.house_age
        house.floor_area = detail.floor_area
        house.land_area = detail.land_area
        house.unit_price = detail.unit_price
        house.floor_number = detail.floor_number
        house.total_floors = detail.total_floors
        house.room_count = detail.room_count
        house.longitude = detail.longitude
        house.latitude = detail.latitude
        house.sold_time = detail.sold_time
        house.house_image = detail.house_image
        
        house.save()
        count += 1
    
    print(f"成功合併 {count} 筆 HouseDetail 數據")


def reverse_merge(apps, schema_editor):
    """
    回退操作（雖然不太可能用到）
    """
    print("警告：無法完全回退數據合併操作")
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('house', '0001_initial'),  # 請改成你最新的 migration 編號
    ]

    operations = [
        # 先添加新欄位到 House（這些在 Model 中已經定義）
        migrations.AddField(
            model_name='house',
            name='city',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='縣市'),
        ),
        migrations.AddField(
            model_name='house',
            name='town',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='行政區'),
        ),
        migrations.AddField(
            model_name='house',
            name='house_age',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='屋齡（年）'),
        ),
        migrations.AddField(
            model_name='house',
            name='floor_area',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='建坪'),
        ),
        migrations.AddField(
            model_name='house',
            name='land_area',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='地坪'),
        ),
        migrations.AddField(
            model_name='house',
            name='unit_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='建坪單價（萬元/坪）'),
        ),
        migrations.AddField(
            model_name='house',
            name='floor_number',
            field=models.IntegerField(blank=True, null=True, verbose_name='所在層數'),
        ),
        migrations.AddField(
            model_name='house',
            name='total_floors',
            field=models.IntegerField(blank=True, null=True, verbose_name='地上總層數'),
        ),
        migrations.AddField(
            model_name='house',
            name='room_count',
            field=models.IntegerField(blank=True, null=True, verbose_name='房間數'),
        ),
        migrations.AddField(
            model_name='house',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=12, max_digits=20, null=True, verbose_name='經度'),
        ),
        migrations.AddField(
            model_name='house',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=12, max_digits=20, null=True, verbose_name='緯度'),
        ),
        migrations.AddField(
            model_name='house',
            name='sold_time',
            field=models.DateField(blank=True, null=True, verbose_name='出售日期'),
        ),
        migrations.AddField(
            model_name='house',
            name='house_image',
            field=models.ImageField(blank=True, null=True, upload_to='house_images/', verbose_name='圖片'),
        ),
        migrations.AddField(
            model_name='house',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='更新時間'),
        ),
        
        # 執行數據遷移
        migrations.RunPython(merge_house_detail_to_house, reverse_merge),
        
        # 刪除 HouseDetail model（取消註釋以執行）
        # migrations.DeleteModel(
        #     name='HouseDetail',
        # ),
    ]
