from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from datetime import timedelta
import uuid

from .models import User, UserProfile, UserSession, EmailVerification, PasswordReset
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserProfileDetailSerializer, ChangePasswordSerializer, UserSessionSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from supermarkets.models import Supermarket


class UserRegistrationView(APIView):
    """User registration endpoint"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate email verification token
            token = str(uuid.uuid4())
            EmailVerification.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            # Send verification email
            try:
                send_mail(
                    'Verify your IMS account',
                    f'Please verify your account by clicking this link: '
                    f'{settings.FRONTEND_URL}/verify-email/{token}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send verification email: {e}")
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully. Please check your email for verification.',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """User login endpoint"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Update last login
            user.last_login = timezone.now()
            user.last_login_ip = self.get_client_ip(request)
            user.save()
            
            # Create user session
            session_key = get_random_string(40)
            UserSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                device_info=self.get_device_info(request)
            )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_device_info(self, request):
        return {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            'accept_encoding': request.META.get('HTTP_ACCEPT_ENCODING', ''),
        }


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    
    serializer_class = UserProfileDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Change password endpoint"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionsView(generics.ListAPIView):
    """List user sessions"""
    
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user, is_active=True)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request, token):
    """Verify email address"""
    try:
        verification = EmailVerification.objects.get(token=token, is_used=False)
        if verification.is_expired:
            return Response({
                'error': 'Verification token has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = verification.user
        user.is_verified = True
        user.save()
        
        verification.is_used = True
        verification.save()
        
        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)
        
    except EmailVerification.DoesNotExist:
        return Response({
            'error': 'Invalid verification token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification_email(request):
    """Resend verification email"""
    email = request.data.get('email')
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        if user.is_verified:
            return Response({
                'message': 'Email is already verified'
            }, status=status.HTTP_200_OK)
        
        # Invalidate old tokens
        EmailVerification.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new token
        token = str(uuid.uuid4())
        EmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Send verification email
        send_mail(
            'Verify your IMS account',
            f'Please verify your account by clicking this link: '
            f'{settings.FRONTEND_URL}/verify-email/{token}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'Verification email sent successfully'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


class PasswordResetRequestView(APIView):
    """Request password reset"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Invalidate old tokens
            PasswordReset.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Generate new token
            token = str(uuid.uuid4())
            PasswordReset.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            
            # Send reset email
            send_mail(
                'Reset your IMS password',
                f'Reset your password by clicking this link: '
                f'{settings.FRONTEND_URL}/reset-password/{token}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return Response({
                'message': 'Password reset email sent successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Confirm password reset"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                reset = PasswordReset.objects.get(token=token, is_used=False)
                if reset.is_expired:
                    return Response({
                        'error': 'Reset token has expired'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user = reset.user
                user.set_password(new_password)
                user.save()
                
                reset.is_used = True
                reset.save()
                
                return Response({
                    'message': 'Password reset successfully'
                }, status=status.HTTP_200_OK)
                
            except PasswordReset.DoesNotExist:
                return Response({
                    'error': 'Invalid reset token'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_session(request, session_id):
    """Logout specific session"""
    try:
        session = UserSession.objects.get(id=session_id, user=request.user)
        session.is_active = False
        session.save()
        
        return Response({
            'message': 'Session logged out successfully'
        }, status=status.HTTP_200_OK)
        
    except UserSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_all_sessions(request):
    """Logout all sessions"""
    UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
    
    return Response({
        'message': 'All sessions logged out successfully'
    }, status=status.HTTP_200_OK)