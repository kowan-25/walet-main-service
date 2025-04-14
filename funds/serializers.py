from rest_framework import serializers
from .models import BudgetRequest, Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'user')

class BudgetRequestSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = BudgetRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'resolve_at', 'requested_by', 'name')

    def get_name(self, obj):
        return obj.requested_by.username if obj.requested_by else ''
