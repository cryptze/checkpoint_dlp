from rest_framework import serializers
from .models import Pattern, DetectedLeak
from datetime import datetime

class PatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pattern
        fields = '__all__'

class DetectedLeakSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectedLeak
        fields = '__all__'

    def to_internal_value(self, data):
        # Convert Slack timestamp (string float) to a datetime object
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                # Convert string float to float, then to datetime
                timestamp_float = float(timestamp_str)
                data['timestamp'] = datetime.fromtimestamp(timestamp_float)
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'timestamp': 'Invalid timestamp format. Expected a string representing a float.'
                })
        
        return super().to_internal_value(data)
