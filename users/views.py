from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import UserRegisterSerializer, ProfileSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        data = request.data
        current_password = data.get('current_password')

        # Validar contraseña actual
        if not current_password or not user.check_password(current_password):
            return Response(
                {"detail": "Contraseña actual requerida para actualizar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lista de campos que pueden ser editados
        allowed_fields = ['username', 'first_name', 'last_name', 'email', 'secret_question', 'password']
        for field in allowed_fields:
            if field in data:
                # Si el campo es 'email', verificar que no esté usado por otro usuario
                if field == 'email' and User.objects.filter(email=data['email']).exclude(id=user.id).exists():
                    return Response(
                        {"detail": "Este correo electrónico ya está en uso."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                setattr(user, field, data[field])

        # Actualizar respuesta secreta (usando método seguro)
        new_secret = data.get('secret_answer')
        if new_secret:
            user.set_secret_answer(new_secret)

        # Cambiar contraseña (opcional)
        new_password = data.get('new_password')
        if new_password:
            user.set_password(new_password)

        user.save()
        return Response(ProfileSerializer(user).data)

    def delete(self, request):
        user = request.user
        password = request.data.get('password')
        if not password or not user.check_password(password):
            return Response({"detail": "Contraseña requerida para eliminar la cuenta."}, status=status.HTTP_400_BAD_REQUEST)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class PasswordResetBySecretView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = request.data.get('identifier')
        if not identifier:
            return Response({"detail": "identificador requerido (username o email)."}, status=400)
        try:
            user = User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                return Response({"detail": "No existe usuario con ese identificador."}, status=400)
        if not user.secret_question:
            return Response({"detail": "Este usuario no tiene pregunta secreta configurada."}, status=400)
        return Response({"secret_question": user.secret_question})


    def put(self, request):
        identifier = request.data.get('identifier')
        answer = request.data.get('answer')
        new_password = request.data.get('new_password')

        if not identifier or not answer or not new_password:
            return Response({"detail": "identifier, answer y new_password requeridos."}, status=400)
        
        try:
            user = User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                return Response({"detail": "No existe usuario con ese identificador."}, status=400)
        if user.check_secret_answer(answer):
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Contraseña actualizada."})
        return Response({"detail": "Respuesta secreta incorrecta."}, status=400)