import base64
from io import BytesIO

import qrcode
from django.conf import settings

from user_profile.models import Card, ProfileCards, UserProfile

url = settings.PROFILE_QRCODE_URL


def create_qr_code(data, box_size=10, border=4):
    qr = qrcode.QRCode(
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    img = qr.make_image(fill_color="black", back_color="white")
    image_file = BytesIO()
    img.save(image_file, format="png")
    image_file.seek(0)
    img_bytes = image_file.read()
    base64_encoded_result_bytes = base64.b64encode(img_bytes)
    return base64_encoded_result_bytes


def create_asset_qr(profile: UserProfile):
    """
    Create QR image file like object
    retruns : image file in base64 bytes
    """
    card = Card.objects.filter(user=profile.user).first()
    if card:
        data = url + f"{card.card}/"

        return create_qr_code(data)


def get_ip_address(request):
    """use requestobject to fetch client machine's IP Address"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")  # Real IP address of client Machine
    return ip


def create_profile_cards(profile):
    data = [
        {"name": "about me", "position": 1},
        {"name": "review links", "position": 2},
        {"name": "social links", "position": 3},
        {"name": "website links", "position": 4},
        {"name": "videos", "position": 5},
        {"name": "contact information", "position": 6},
    ]
    data = ProfileCards(profile=profile, data=data)
    data.save()
