from rest_framework import serializers
from .models import BudgetRequest, Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'user')

class BudgetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'resolve_at', 'requested_by')