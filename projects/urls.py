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
    path('invite-member', InviteTeamMember.as_view(), name='invite-team-member'),
    path('add-member/<uuid:token>', AddTeamMember.as_view(), name='add-team-member'),
    path('budget-records/<uuid:project_id>', GetProjectBudgets.as_view(), name='project-budgets'),
    path('budget-record/<uuid:pk>', GetProjectBudgetById.as_view(), name='project-budget-detail'),
    path('budget-record/create', AddProjectBudget.as_view(), name='create-project-budget'),
    path('budget-record/edit/<uuid:pk>', UpdateProjectBudget.as_view(), name='edit-project-budget'),
    path('budget-record/delete/<uuid:pk>', DeleteProjectBudget.as_view(), name='delete-project-budget'),
    path('analytics/<uuid:project_id>', GetProjectAnalytics.as_view(), name='project-analytics'),
]