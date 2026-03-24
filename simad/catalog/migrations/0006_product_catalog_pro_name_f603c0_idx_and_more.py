import django.contrib.postgres.indexes
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_wishlist'),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['name'], name='catalog_pro_name_f603c0_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['slug'], name='catalog_pro_slug_2b1eb6_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['created'], name='catalog_pro_created_ac00b7_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=django.contrib.postgres.indexes.GinIndex(fields=['name', 'description'], name='catalog_pro_name_94277b_gin', opclasses=['gin_trgm_ops', 'gin_trgm_ops']),
        ),
    ]
