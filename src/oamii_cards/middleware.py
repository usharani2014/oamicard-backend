import time

from authentication.models import Request
from user_profile.service import get_ip_address


class SaveRequest:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _t = time.time()  # Calculated execution time.
        response = self.get_response(request)  # Get response from view function.
        _t = int((time.time() - _t) * 1000)

        # If the url does not start with on of the prefixes above, then return response and dont save log.
        if request.get_full_path().startswith("/api/admin"):
            return response

        # Create instance of our model and assign values
        try:
            request_log = Request(
                endpoint=request.get_full_path(),
                response_code=response.status_code,
                method=request.method,
                remote_address=get_ip_address(request),
                exec_time=_t,
                body_response=str(response.content),
                body_request=dict(request.POST),
            )

            # Assign user to log if it's not an anonymous user
            if not request.user.is_anonymous:
                request_log.user = request.user

            # Save log in db
            request_log.save()
        except Exception:
            pass
        return response
