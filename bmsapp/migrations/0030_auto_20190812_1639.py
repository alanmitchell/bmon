# Generated by Django 2.1.7 on 2019-08-13 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmsapp', '0029_auto_20190812_1607'),
    ]

    operations = [
        migrations.AlterField(
            model_name='building',
            name='building_type',
            field=models.CharField(blank=True, choices=[('S-RES', 'Single-Family Residential'), ('M-RES', 'Multi-Family Residential'), ('OFFIC', 'Office'), ('SCH', 'School'), ('RET', 'Retail'), ('RES', 'Restaurant'), ('WARE', 'Warehouse'), ('INDUS', 'Industrial'), ('OTHER', 'Other')], max_length=5, null=True, verbose_name='Building Type'),
        ),
    ]