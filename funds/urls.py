from django.urls import path

from funds.views import SendFunds

urlpatterns = [
    path('send-funds/<uuid:project_id>', SendFunds.as_view(), name='send-funds'),
]