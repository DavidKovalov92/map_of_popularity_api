from redis import AuthenticationError
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator

User = get_user_model()

class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "password", "email")

    def validate(self, data):
        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError("Username already taken.")
        return data

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data["email"],
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data["user"] = user
        return data


class LogoutSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)

    def validate_user_id(self, value):
        if value and value == self.context["request"].user.id:
            raise serializers.ValidationError("You cannot log out another user.")
        return value


class RequestPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ("email",)



class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    token = serializers.CharField(max_length=555, write_only=True)
    uidb64 = serializers.CharField(max_length=555, write_only=True)

    class Meta:
        fields = ("password", "token", "uidb64")

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            token = attrs.get("token")
            uidb64 = attrs.get("uidb64")

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationError("Token is invalid or expired.")
            
            user.set_password(password)
            user.save()
            
            return (user)
        except Exception as e:
            raise AuthenticationError("Link is invalid", 401)
