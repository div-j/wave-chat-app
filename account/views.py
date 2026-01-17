from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view

from account.responseSerializers import (ResponseSerializer, ErrorResponseSerializer)


from .serializers import (
    EmailTokenObtainPairSerializer, RegisterSerializer, UserSerializer)
from account.models import User



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