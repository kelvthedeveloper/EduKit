from rest_framework import serializers
from ..models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_uuid = serializers.UUIDField(source='actor.uuid', allow_null=True, read_only=True)

    class Meta:
        model = AuditEvent
        fields = (
            'uuid',
            'actor_uuid',
            'actor_email',
            'action',
            'resource_type',
            'resource_id',
            'status',
            'ip_address',
            'user_agent',
            'details',
            'created_at',
        )
        read_only_fields = fields
