from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=True, validators=[
        UniqueValidator(queryset=User.objects.all())
    ],
    write_only=True
    )
    password = serializers.CharField(min_length=6, max_length=100, write_only=True)
    confirm_password = serializers.CharField(min_length=6, max_length=100, write_only=True)
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'confirm_password'
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    def validate(self, attrs):
        if getattr(attrs, 'password') != getattr(attrs, 'confirm_password'):
            raise serializers.ValidationError("Password and Confirm Password doesnot match.")
        return attrs

class CustomTokenObtainPairSerilizer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['id'] = self.user.id
        return data