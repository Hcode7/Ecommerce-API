from rest_framework import serializers
from django.contrib.auth.models import User

class UserCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email' ,'password']
        extra_kwargs = {'password' : {'write_only' : True}}

        def create(self, validted_data):
            user = User.objects.create_user(
                username=validted_data['username'],
                email=validted_data['email'],
                password=validted_data['password']
            )
            return user