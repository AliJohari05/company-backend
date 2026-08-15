from rest_framework import permissions


class IsAdminOrAuthor(permissions.BasePermission):
    """
    Custom permission to only allow admins or the author of an object to edit/delete it,
    and only allow admins/staff to create new objects.
    """

    def has_permission(self, request, view):
        # Read-only requests are allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Must be authenticated for any write action
        if not request.user or not request.user.is_authenticated:
            return False

        # For creating new posts (POST), only staff/admin is allowed
        if request.method == 'POST':
            return request.user.is_staff or request.user.is_superuser

        return True

    def has_object_permission(self, request, view, obj):
        # Read-only requests are allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `author`
        # Staff/Admins or the owner/author of the post can edit/delete it
        return (
            request.user.is_staff or 
            request.user.is_superuser or 
            getattr(obj, 'author', None) == request.user
        )