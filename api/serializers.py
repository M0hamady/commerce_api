
from rest_framework import serializers
from .models import   User

class UserImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['image_url']

    def validate_image(self, value):
        # Add any custom image validation logic here
        # For example, you can check the image size, file format, or perform any other checks

        # Here's an example of checking the image size
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError("Image size exceeds the maximum allowed size.")

        return value

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        required=True
    )

    email = serializers.EmailField(
        max_length=255,
        min_length=6,
        required=False
    )

    first_name = serializers.CharField(
        max_length=30,
        required=False
    )

    last_name = serializers.CharField(
        max_length=30,
        required=False
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        # Additional field-level validation can be performed here
        # Example: Ensure username is unique
        username = attrs.get('username')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError('Username is already taken.')

        # You can add more validation logic for other fields as needed

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data, is_client=True)
        return user
 
 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'  # You can specify particular fields if needed   
    
    
    
    
    
    