from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_bytes, smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse


from account.responseSerializers import (
    ResponseSerializer, 
    ErrorResponseSerializer
    )

from .serializers import (
    EmailTokenObtainPairSerializer, 
    RegisterSerializer, 
    UserSerializer,
    RequestPasswordResetEmailSerializer,
    SetNewPasswordSerializer
    )

from account.models import User

from lib.utils import send_email



@extend_schema_view(
    post=extend_schema(
        request=RegisterSerializer,
        responses={201: ResponseSerializer, 400: ErrorResponseSerializer},
        description="Register a new user with email and password.",
        summary="User Registration"
    )
)
class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []

    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "email": user.email
                }
            },
            status=status.HTTP_201_CREATED
        )

@extend_schema_view(
    post=extend_schema(
        request=EmailTokenObtainPairSerializer,
        responses={200: ResponseSerializer, 400: ErrorResponseSerializer},
        description="Obtain JWT token pair using email and password.",
        summary="User Login"
    )
)
class EmailLoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    


@extend_schema_view(
    list=extend_schema(
        responses={200: UserSerializer, 404: ErrorResponseSerializer},
        description="Retrieve the profile of the authenticated user.",
        summary="Get User Profile"
    ),
    update=extend_schema(
        responses={200: UserSerializer, 400: ErrorResponseSerializer},
        description="Update the authenticated user's profile.",
        summary="Update User Profile"
    ),
    partial_update=extend_schema(
        responses={200: UserSerializer, 400: ErrorResponseSerializer},
        description="Partially update the authenticated user's profile.",
        summary="Partial Update User Profile"
    )
)
class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

@extend_schema_view(
    post=extend_schema(
        request=RequestPasswordResetEmailSerializer,
        responses={200: ResponseSerializer, 400: ErrorResponseSerializer},
        description="Request a password reset email.",
        summary="Request Password Reset"
    )
)
class RequestPasswordResetEmail(CreateAPIView):
    serializer_class = RequestPasswordResetEmailSerializer
    permission_classes = []

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data.get('email', '')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            # Generate password reset link
            current_site = get_current_site(request).domain
            relativeLink = reverse('reset-password-confirm', kwargs={'uidb64': uidb64, 'token': token})
            absurl = 'http://' + current_site + relativeLink
            email_body = f'Hello, \n\nUse the link below to reset your password:\n{absurl}\n\nIf you did not request this, please ignore this email.'
            
            # Send email (prints to console in dev)
            print(f"DEBUG: Sending email to {user.email}") # Added debug print
            send_email(
                subject="Reset your password",
                message=email_body,
                from_email="noreply@engitech.com",
                recipient_list=[user.email]
            )
        else:
            print(f"DEBUG: User with email '{email}' not found") # Added debug print

        return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)


@extend_schema_view(
    patch=extend_schema(
        request=SetNewPasswordSerializer,
        responses={200: ResponseSerializer, 400: ErrorResponseSerializer},
        description="Set a new password using the reset token.",
        summary="Set New Password"
    )
)

class SetNewPasswordAPIView(CreateAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = []

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)