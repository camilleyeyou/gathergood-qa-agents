from rest_framework.permissions import BasePermission


def get_member_role(user, organization):
    from apps.organizations.models import OrganizationMember
    try:
        return OrganizationMember.objects.get(user=user, organization=organization).role
    except OrganizationMember.DoesNotExist:
        return None


class IsOrgOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return get_member_role(request.user, obj) == 'OWNER'


class IsOrgOwnerOrManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        return get_member_role(request.user, obj) in ('OWNER', 'MANAGER')


class IsOrgMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        return get_member_role(request.user, obj) is not None
