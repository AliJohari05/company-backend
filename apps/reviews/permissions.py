from rest_framework.permissions import BasePermission


class ReviewPermission(BasePermission):
    def has_permission(self, request, view):
        return request.method == "GET" or bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.method == "GET" or request.user.is_staff or obj.user_id == request.user.id
