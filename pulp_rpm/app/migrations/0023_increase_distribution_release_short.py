# Generated by Django 2.2.16 on 2020-09-18 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rpm', '0022_add_collections_related_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributiontree',
            name='base_product_short',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='distributiontree',
            name='release_short',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='image',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
