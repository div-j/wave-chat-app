from rest_framework import serializers


class ResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = serializers.DictField()

class ErrorResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    status_code = serializers.IntegerField()
    message = serializers.CharField()
    details = serializers.CharField()


