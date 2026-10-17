from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.views import PasswordChangeView
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy

from .models import User


class OwnPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(User).pk,
            object_id=str(self.request.user.pk),
            object_repr=self.request.user.username,
            action_flag=CHANGE,
            change_message="用户修改了自己的登录密码。",
        )
        return response
