from django.db import models

# Create your models here.
class Visitor(models.Model):
    name = models.CharField(verbose_name="Visitor Name", max_length=100)
    telephone = models.CharField(verbose_name="Visitor Telephone", max_length=100)
    purpose = models.CharField(verbose_name="Purpose of Visit", max_length=100)
    images_collected = models.TextField(verbose_name="Base64 Encodings")

    def __str__(self) -> str:
        return self.name


class VisitorLog(models.Model):
    person_to_see = models.CharField(verbose_name="Person Visited", max_length=100)
    visitor_fk = models.ForeignKey(Visitor, on_delete=models.DO_NOTHING)
    vistor_name = models.CharField(max_length=100)
    time_in = models.DateTimeField(verbose_name="Time In", auto_now_add=True)
    time_out = models.DateTimeField(verbose_name="Time Out", blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.vistor_name} came to see {self.person_to_see} at {self.time_in}"
