from django.urls import path

from.views import ( GetUserBudgetRequests, GetProjectTransaction, GetMemberTransaction, GetBudgetRequestById, GetUserBudgetRequestsByProjectId, GetTransactionById, CreateTransaction, DeleteTransaction, SendFunds, ResolveBudgetRequest, TakeFunds, UpdateTransaction
                   )

urlpatterns = [
    path('<uuid:project_id>', GetProjectTransaction.as_view(), name='project-transaction-list'),
    path('<uuid:project_id>/<uuid:user_id>', GetMemberTransaction.as_view(), name='member-transaction-list'),
    path('<uuid:pk>', GetTransactionById.as_view(), name='transaction-detail'),
    path('create', CreateTransaction.as_view(), name='create-transaction'),
    path('delete/<uuid:pk>', DeleteTransaction.as_view(), name='delete-transaction'),
    path('edit/<uuid:pk>', UpdateTransaction.as_view(), name='edit-transaction'),
    path('send-funds/<uuid:project_id>', SendFunds.as_view(), name='send-funds'),
    path('take-funds/<uuid:project_id>', TakeFunds.as_view(), name='take-funds'),
    path('budget-requests', GetUserBudgetRequests.as_view(), name='budget-request-list'),
    path('budget-requests/<uuid:project_id>', GetUserBudgetRequestsByProjectId.as_view(), name='budget-request-list-by-project'),
    path('budget-requests/<uuid:pk>', GetBudgetRequestById.as_view(), name='budget-request-detail'),
    path('budget-requests/resolve/<uuid:pk>', ResolveBudgetRequest.as_view(), name='resolve-budget-request'),
]