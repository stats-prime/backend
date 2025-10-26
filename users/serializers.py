from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    secret_answer = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password', 'password2', 'first_name', 'last_name',
            'secret_question', 'secret_answer'
        )
        extra_kwargs = {
            'email': {'required': True},
        }

    # Validar contraseñas iguales
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs
    
    # Validar username único (sin distinción de mayúsculas/minúsculas)
    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value
    
    # Validar email único (sin distinción de mayúsculas/minúsculas)
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("El correo ya está en uso.")
        return value
    
    # Crear usuario con contraseña y respuesta secreta seguras
    def create(self, validated_data):
        validated_data.pop('password2', None)
        raw_password = validated_data.pop('password')
        raw_secret = validated_data.pop('secret_answer', None)
        
        user = User(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            secret_question=validated_data.get('secret_question', None),
        )

        user.set_password(raw_password)

        # Hashear respuesta secreta si existe
        if raw_secret and hasattr(user, 'set_secret_answer'):
            user.set_secret_answer(raw_secret)


        user.save()
        return user

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'secret_question')
        read_only_fields = ('username', 'email')