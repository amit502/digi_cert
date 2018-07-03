from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    issuer_url = models.CharField(max_length=200, blank=False, default="")
    issuer_email = models.EmailField(blank=False, default="")
    issuer_id = models.CharField( max_length=200,blank=False, default="")
    revocation_list = models.CharField(max_length=200,blank=False, default="")
    issuer_public_key = models.CharField(max_length=128, blank=False, default="")
    certificate_description = models.TextField(blank=False, default="")
    certificate_title = models.CharField(max_length=200, blank=False, default="")
    criteria_narrative = models.TextField(blank=False,default="")
    badge_id = models.CharField(max_length=32, default="")
    issuer_logo_file = models.ImageField(blank=False,default="", upload_to="images")
    cert_image_file = models.ImageField(blank=False, default="",upload_to="images")
    issuer_signature_file = models.ImageField(blank=False,default="",upload_to="images")

    def __str__(self):
        """
        String for representing the MyModelName object (in Admin site etc.)
        """
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
