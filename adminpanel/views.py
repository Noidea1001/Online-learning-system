# adminpanel/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

User = get_user_model()


def superuser_required(view_func):
    """Restrict a view to superusers only, matching the rest of the project's
    permission style (raise/forbid rather than redirect to login)."""
    decorated = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='login'
    )(view_func)
    return decorated


# ──────────────────────────────────────────────────────────
#  CONTROL CENTER HOME
# ──────────────────────────────────────────────────────────
@login_required
@superuser_required
def control_center(request):
    total_users = User.objects.count()
    total_groups = Group.objects.count()
    total_permissions = Permission.objects.count()
    staff_count = User.objects.filter(is_staff=True).count()
    superuser_count = User.objects.filter(is_superuser=True).count()
    active_count = User.objects.filter(is_active=True).count()
    inactive_count = total_users - active_count

    role_counts = {
        'STUDENT': User.objects.filter(role='STUDENT').count(),
        'INSTRUCTOR': User.objects.filter(role='INSTRUCTOR').count(),
        'EMPLOYEE': User.objects.filter(role='EMPLOYEE').count(),
    }

    groups = Group.objects.annotate(
        member_count=Count('user', distinct=True),
        perm_count=Count('permissions', distinct=True)
    ).order_by('name')

    recent_users = User.objects.order_by('-date_joined')[:6]

    from .models import AuditLog
    recent_logs = AuditLog.objects.select_related('actor', 'content_type').all()[:8]

    context = {
        'total_users': total_users,
        'total_groups': total_groups,
        'total_permissions': total_permissions,
        'staff_count': staff_count,
        'superuser_count': superuser_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'role_counts': role_counts,
        'groups': groups,
        'recent_users': recent_users,
        'recent_logs': recent_logs,
    }
    return render(request, 'adminpanel/control_center.html', context)


# ──────────────────────────────────────────────────────────
#  USERS

from django.db.models import Value
from django.db.models.functions import Concat

@login_required
@superuser_required
def user_list(request):
    queryset = User.objects.all().prefetch_related('groups').order_by('-date_joined')

    search_query = request.GET.get('search', '').strip()
    if search_query:
        # បង្កើត Field ថ្មីមួយបណ្តោះអាសន្ន (full_name) ដោយបូកបញ្ចូល first_name និង last_name ចូលគ្នា
        # ដើម្បីឱ្យអ្នកប្រើប្រាស់អាចស្វែងរកឈ្មោះពេញ (First Name + Last Name) បានយ៉ាងត្រឹមត្រូវ
        queryset = queryset.annotate(
            full_name_1=Concat('first_name', Value(' '), 'last_name'),
            full_name_2=Concat('last_name', Value(' '), 'first_name')
        ).filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(full_name_1__icontains=search_query) |
            Q(full_name_2__icontains=search_query)
        )

    role_filter = request.GET.get('role', '').strip()
    if role_filter:
        queryset = queryset.filter(role=role_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    elif status_filter == 'staff':
        queryset = queryset.filter(is_staff=True)
    elif status_filter == 'superuser':
        queryset = queryset.filter(is_superuser=True)

    paginator = Paginator(queryset, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'role_choices': User.Role.choices,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'adminpanel/includes/user_table_partial.html', context)
        
    return render(request, 'adminpanel/user_list.html', context)


@login_required
@superuser_required
def user_permissions_detail(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    all_groups = Group.objects.all().order_by('name')
    user_group_ids = set(user_obj.groups.values_list('id', flat=True))

    if request.method == 'POST':
        # Account flags
        new_role = request.POST.get('role')
        if new_role in dict(User.Role.choices):
            user_obj.role = new_role

        user_obj.is_active = request.POST.get('is_active') == 'on'
        user_obj.is_staff = request.POST.get('is_staff') == 'on'

        # Prevent a superuser from accidentally locking themselves out
        if user_obj == request.user and request.POST.get('is_superuser') != 'on':
            messages.error(request, "You can't remove your own superuser status.")
        else:
            user_obj.is_superuser = request.POST.get('is_superuser') == 'on'

        user_obj.save()

        # Group assignment
        selected_group_ids = request.POST.getlist('groups')
        user_obj.groups.set(selected_group_ids)

        messages.success(request, f"Permissions updated for {user_obj.username}.")
        return redirect('adminpanel_user_detail', pk=user_obj.pk)

    context = {
        'user_obj': user_obj,
        'all_groups': all_groups,
        'user_group_ids': user_group_ids,
        'role_choices': User.Role.choices,
    }
    return render(request, 'adminpanel/user_detail.html', context)


# ──────────────────────────────────────────────────────────
#  GROUPS & PERMISSIONS
# ──────────────────────────────────────────────────────────
@login_required
@superuser_required
def group_list(request):
    groups = Group.objects.annotate(
        member_count=Count('user', distinct=True),
        perm_count=Count('permissions', distinct=True)
    ).order_by('name')
    return render(request, 'adminpanel/group_list.html', {'groups': groups})


@login_required
@superuser_required
def group_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        selected_perm_ids = request.POST.getlist('permissions')
        if not name:
            messages.error(request, "Group name is required.")
        elif Group.objects.filter(name__iexact=name).exists():
            messages.error(request, f"A group named '{name}' already exists.")
        else:
            group = Group.objects.create(name=name)
            if selected_perm_ids:
                group.permissions.set(selected_perm_ids)
            messages.success(request, f"Group '{name}' created successfully.")
            return redirect('adminpanel_group_detail', pk=group.pk)

        grouped_permissions = _grouped_permissions()
        return render(request, 'adminpanel/group_form.html', {
            'grouped_permissions': grouped_permissions,
            'group_perm_ids': {int(i) for i in selected_perm_ids},
            'title': 'Create Group',
            'group': None,
        })

    grouped_permissions = _grouped_permissions()
    return render(request, 'adminpanel/group_form.html', {
        'grouped_permissions': grouped_permissions,
        'group_perm_ids': set(),
        'title': 'Create Group',
        'group': None,
    })


@login_required
@superuser_required
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        selected_perm_ids = request.POST.getlist('permissions')
        if not name:
            messages.error(request, "Group name is required.")
        elif Group.objects.filter(name__iexact=name).exclude(pk=group.pk).exists():
            messages.error(request, f"A group named '{name}' already exists.")
        else:
            group.name = name
            group.save()
            group.permissions.set(selected_perm_ids)
            messages.success(request, f"Group '{name}' updated successfully.")
            return redirect('adminpanel_group_detail', pk=group.pk)

        grouped_permissions = _grouped_permissions()
        members = group.user_set.all().order_by('username')
        return render(request, 'adminpanel/group_form.html', {
            'grouped_permissions': grouped_permissions,
            'group_perm_ids': {int(i) for i in selected_perm_ids},
            'title': f'Edit Group — {group.name}',
            'group': group,
            'members': members,
        })

    grouped_permissions = _grouped_permissions()
    group_perm_ids = set(group.permissions.values_list('id', flat=True))
    members = group.user_set.all().order_by('username')

    return render(request, 'adminpanel/group_form.html', {
        'grouped_permissions': grouped_permissions,
        'group_perm_ids': group_perm_ids,
        'title': f'Edit Group — {group.name}',
        'group': group,
        'members': members,
    })


@login_required
@superuser_required
@require_POST
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    name = group.name
    group.delete()
    messages.success(request, f"Group '{name}' deleted.")
    return redirect('adminpanel_group_list')


def _grouped_permissions():
    """Return all Permission objects grouped by their app/model content type,
    so the template can render a checkbox matrix organised by app."""
    permissions = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'codename'
    )
    grouped = {}
    for perm in permissions:
        app_label = perm.content_type.app_label
        model_name = perm.content_type.model
        key = f"{app_label}.{model_name}"
        grouped.setdefault(key, {
            'app_label': app_label,
            'model_name': model_name,
            'permissions': []
        })
        grouped[key]['permissions'].append(perm)
    return grouped


# ──────────────────────────────────────────────────────────
#  AUDIT LOG
# ──────────────────────────────────────────────────────────
@login_required
@superuser_required
def audit_log_list(request):
    from django.contrib.contenttypes.models import ContentType
    from .models import AuditLog

    queryset = AuditLog.objects.select_related('actor', 'content_type').all()

    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(object_repr__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(actor__username__icontains=search_query)
        )

    action_filter = request.GET.get('action', '').strip()
    if action_filter:
        queryset = queryset.filter(action=action_filter)

    model_filter = request.GET.get('model', '').strip()
    if model_filter:
        queryset = queryset.filter(content_type__model=model_filter)

    date_from = request.GET.get('date_from', '').strip()
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)

    date_to = request.GET.get('date_to', '').strip()
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    tracked_content_types = ContentType.objects.filter(
        id__in=AuditLog.objects.exclude(content_type__isnull=True)
        .values_list('content_type', flat=True).distinct()
    ).order_by('model')

    context = {
        'page_obj': page_obj,
        'logs': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'action_choices': AuditLog.Action.choices,
        'tracked_content_types': tracked_content_types,
        'search_query': search_query,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'adminpanel/audit_log_list.html', context)
