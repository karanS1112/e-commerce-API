import razorpay

from app.core.config import settings

#initialize razorpay client with the key and secret from settings
razorpay_client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)