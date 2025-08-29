from ninja_jwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 커스텀 정보 추가
        token['username'] = user.username
        token['name'] = user.name
        token['email'] = user.email
        token['role'] = user.role
        return token 