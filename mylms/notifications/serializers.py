from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'notification_type', 
                  'is_read', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        # Set the user to the current request user unless specifically provided
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        
        return super().create(validated_data)