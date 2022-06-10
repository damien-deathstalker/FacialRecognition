# Generated by Django 4.0.2 on 2022-02-09 14:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Registration', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='visitor',
            name='person_to_see',
        ),
        migrations.CreateModel(
            name='VisitorLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('person_to_see', models.CharField(max_length=100, verbose_name='Person Visited')),
                ('vistor_name', models.CharField(max_length=100)),
                ('time_in', models.DateTimeField(auto_now_add=True, verbose_name='Time In')),
                ('time_out', models.DateTimeField(blank=True, null=True, verbose_name='Time Out')),
                ('visitor_fk', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='Registration.visitor')),
            ],
        ),
    ]