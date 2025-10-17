from rest_framework import serializers  # type: ignore

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ["id", "email", "password"]

    def update(self, instance, validated_data):
        print("Updating via serializer")

        # Pop password if it exists to handle separately
        password = validated_data.pop("password", None)

        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Safely set password using Django's set_password method
        if password:
            instance.set_password(password)

        instance.save()
        print(instance.password, instance.email)  # optional debug
        return instance
