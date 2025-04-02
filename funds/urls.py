from django.urls import path

from funds.views import CreateTransaction, GetBudgetRequestById, GetUserBudgetRequests, SendFunds

urlpatterns = [
    path('send-funds/<uuid:project_id>', SendFunds.as_view(), name='send-funds'),
    path('budget-requests', GetUserBudgetRequests.as_view(), name='budget-request-list'),
    path('budget-requests/<uuid:pk>', GetBudgetRequestById.as_view(), name='budget-request-detail'),
    path('create', CreateTransaction.as_view(), name='create-transaction'),
]