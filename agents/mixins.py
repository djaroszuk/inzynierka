from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import render


# Mixin for logged in organisor
class OrganisorAndLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is an organisor."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_organisor:
            return render(
                request,
                "403_forbidden.html",
                {"message": "You do not have permission to access this page."},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)
