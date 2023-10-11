from django.contrib.auth.models import User
from django.db import models

from oamii_cards.models import DatetimeModel


class InvitationCode(DatetimeModel):
    first_name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    is_used = models.BooleanField(default=False)
    email = models.EmailField()


class Request(DatetimeModel):
    endpoint = models.CharField(max_length=100, null=True)  # The url the user requested
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )  # User that made request, if authenticated
    response_code = models.PositiveSmallIntegerField()  # Response status code
    method = models.CharField(max_length=10, null=True)  # Request method
    remote_address = models.CharField(max_length=20, null=True)  # IP address of user
    exec_time = models.IntegerField(null=True)  # Time taken to create the response
    date = models.DateTimeField(auto_now=True)  # Date and time of request
    body_response = models.TextField()  # Response data
    body_request = models.TextField()  # Request data
