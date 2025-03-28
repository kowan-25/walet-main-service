from django.urls import path

from.views import *

urlpatterns = [
    path('managed', GetAllManagedProject.as_view(), name='projects-managed-list'),
    path('joined', GetAllJoinedProject.as_view(), name='projects-joined-list'),
    path('<uuid:pk>', GetProjectById.as_view(), name='project-detail'),
    path('create', CreateProject.as_view(), name='create-project'),
    path('delete/<uuid:pk>', DeleteProject.as_view(), name='delete-project'),
    path('edit/<uuid:pk>', UpdateProject.as_view(), name='edit-project'),
    path('categories/<uuid:project_id>', GetProjectCategories.as_view(), name='project-categories-list'),
    path('category/<uuid:pk>', GetProjectCategoryById.as_view(), name='project-category-detail'),
    path('category/create', CreateProjectCategory.as_view(), name='create-project-category'),
    path('category/delete/<uuid:pk>', DeleteProjectCategory.as_view(), name='delete-project-category'),
    path('<uuid:project_pk>/members/<uuid:member_pk>', RemoveTeamMember.as_view(), name='remove-team-member'),
]