from rest_framework import serializers


class EmailVerifyRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)


class EmailVerifyConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128, required=True)


class PhoneVerifyRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)


class PhoneVerifyConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, required=True)
    code = serializers.CharField(max_length=8, required=True)
