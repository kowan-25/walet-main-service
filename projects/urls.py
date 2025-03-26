from django.urls import path

from.views import *

urlpatterns = [
    path('managed', GetAllManagedProject.as_view(), name='projects-managed-list'),
    path('create', CreateProject.as_view(), name='create-project'),
    path('delete/<uuid:pk>', DeleteProject.as_view(), name='delete-project'),
    path('edit/<uuid:pk>', UpdateProject.as_view(), name='edit-project'),
    
]