from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from account.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"]
        )
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'


class RequestPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        fields = ['email']

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            try:
                id = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(id=id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
                print(f"DEBUG: Error decoding uid or finding user: {e}")
                raise serializers.ValidationError('Invalid UID', code='authorization')

            # Clean up token (remove potential copy-paste artifacts like =)
            token = token.replace('=', '')

            if not PasswordResetTokenGenerator().check_token(user, token):
                print(f"DEBUG: Token check failed for user {user.email} with token {token}")
                raise serializers.ValidationError('The reset link is invalid', code='authorization')

            user.set_password(password)
            user.save()
            return attrs
        except Exception as e:
            print(f"DEBUG: Unexpected error in SetNewPasswordSerializer: {e}")
            raise serializers.ValidationError(f'The reset link is invalid: {e}', code='authorization')
        return super().validate(attrs)