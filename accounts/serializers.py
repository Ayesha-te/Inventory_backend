from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, UserSession


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 
            'password', 'password_confirm', 'phone', 'company_name'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    subscription_days_remaining = serializers.ReadOnlyField(source='get_subscription_days_remaining')
    is_subscription_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'company_name', 'address', 'profile_picture',
            'subscription_plan', 'subscription_start_date', 'subscription_end_date',
            'is_subscription_active', 'subscription_days_remaining', 'is_subscription_expired',
            'timezone', 'language', 'email_notifications', 'is_verified',
            'registration_date', 'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'registration_date', 'last_login',
            'subscription_plan', 'subscription_start_date', 'subscription_end_date',
            'is_subscription_active', 'is_verified'
        ]


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for user profile with extended info"""
    
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'company_name', 'address', 'profile_picture',
            'subscription_plan', 'subscription_start_date', 'subscription_end_date',
            'is_subscription_active', 'timezone', 'language', 'email_notifications',
            'is_verified', 'registration_date', 'last_login', 'profile'
        ]
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'bio': profile.bio,
                'birth_date': profile.birth_date,
                'website': profile.website,
                'business_type': profile.business_type,
                'tax_id': profile.tax_id,
                'low_stock_alerts': profile.low_stock_alerts,
                'expiry_alerts': profile.expiry_alerts,
                'pos_sync_alerts': profile.pos_sync_alerts,
                'weekly_reports': profile.weekly_reports,
            }
        except UserProfile.DoesNotExist:
            return None


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions"""
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'session_key', 'ip_address', 'user_agent',
            'device_info', 'location', 'created_at', 'last_activity', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity']


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs