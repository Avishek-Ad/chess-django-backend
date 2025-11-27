from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import Q, F

class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        username = email.split("@")[0]
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)
    
class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.username



# the below models are not being used currently but will use in later version

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    displayname = models.CharField(max_length=30, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.user)
    
    @property
    def avatar_url(self):
        if not self.avatar:
            return ""
        url = self.avatar.url
        return url
    
class FriendRequest(models.Model):
    sender = models.ForeignKey(User, related_name="sent_friend_requests", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_friend_requests", on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver') # prevents duplicate requests
        constraints = [
            # prevent self request
            models.CheckConstraint(check=~Q(sender=F('receiver')), name='prevent_self_request')
        ]

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"