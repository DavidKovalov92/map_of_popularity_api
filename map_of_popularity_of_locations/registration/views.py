from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from .tasks import send_subcribe_email
from .utils import Util
from .serializers import (
    LogoutSerializer,
    RequestPasswordEmailRequestSerializer,
    SetNewPasswordSerializer,
    SignUpSerializer,
    LoginSerializer,
)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, smart_str, DjangoUnicodeDecodeError
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView


class SignUpView(APIView):
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User successfully created. Please log in."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)
            return Response({"message": "Login successful."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        logout(request)
        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)


class RequestPasswordResetEmailGenericView(GenericAPIView):
    serializer_class = RequestPasswordEmailRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data["email"]
        User = get_user_model()

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request=request).domain
            relativeLink = reverse(
                "reset-password-confirm", kwargs={"uidb64": uidb64, "token": token}
            )
            absurl = "http://" + current_site + relativeLink
            email_body = "Hello, \n Use link below to reset your password \n" + absurl

            send_subcribe_email.delay(email_body=email_body, user_email=user.email)
        return Response(
            {"success": "We have sent you a link to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordTokenCheckGenericView(GenericAPIView):
    def get(self, request, uidb64, token):
        User = get_user_model()
        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {"error": "Token is not valid"}, status=status.HTTP_401_UNAUTHORIZED
                )

            return Response(
                {
                    "success": True,
                    "message": "Credentials are valid",
                    "uidb64": uidb64,
                    "token": token,
                },
                status=status.HTTP_200_OK,
            )

        except DjangoUnicodeDecodeError as identifier:
            return Response(
                {"error": "Token is not valid"}, status=status.HTTP_401_UNAUTHORIZED
            )


class SetNewPasswordGenericView(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"success": True, "message": "Password reset success"},
            status=status.HTTP_200_OK,
        )
