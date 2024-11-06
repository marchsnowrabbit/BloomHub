# Generated by Django 4.1.13 on 2024-11-04 14:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("BloomHub", "0004_bloomuser_groups_bloomuser_user_permissions"),
    ]

    operations = [
        migrations.CreateModel(
            name="BloomDictionary",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("language", models.CharField(max_length=10)),
                ("stage", models.CharField(max_length=50)),
                ("words", models.JSONField()),
            ],
        ),
        migrations.CreateModel(
            name="LearningVideo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("vid", models.CharField(max_length=100, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("setTime", models.IntegerField()),
                ("uploader", models.CharField(blank=True, max_length=255, null=True)),
                ("view_count", models.IntegerField(default=0)),
                ("std_lang", models.CharField(default="EN", max_length=10)),
                ("learning_status", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        to_field="user_id",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WordData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("word", models.CharField(max_length=255)),
                ("pos", models.CharField(max_length=50)),
                ("start_time", models.IntegerField()),
                ("end_time", models.IntegerField()),
                ("page_rank", models.FloatField(blank=True, null=True)),
                ("url", models.URLField(blank=True, null=True)),
                ("data_type", models.CharField(default="word", max_length=10)),
                (
                    "video",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="word_data",
                        to="BloomHub.learningvideo",
                        to_field="vid",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SentenceData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("word", models.TextField()),
                ("start_time", models.IntegerField()),
                ("end_time", models.IntegerField()),
                ("data_type", models.CharField(default="sentence", max_length=10)),
                (
                    "video",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sentence_data",
                        to="BloomHub.learningvideo",
                        to_field="vid",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AnalysisResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bloom_stage_segments", models.JSONField()),
                ("top_nouns", models.JSONField()),
                ("donut_chart", models.JSONField()),
                ("dot_chart", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "video",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis_results",
                        to="BloomHub.learningvideo",
                        to_field="vid",
                    ),
                ),
            ],
        ),
    ]
