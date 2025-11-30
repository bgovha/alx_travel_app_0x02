from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_payment_confirmation_email(user_email, booking_reference, amount):
    """
    Send payment confirmation email asynchronously
    """
    try:
        subject = 'Payment Confirmation - ALX Travel App'
        message = f'''
        Dear Customer,

        Your payment has been successfully processed.

        Booking Reference: {booking_reference}
        Amount Paid: {amount} ETB

        Thank you for choosing ALX Travel App!

        Best regards,
        ALX Travel Team
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        
        logger.info(f"Payment confirmation email sent to {user_email}")
        
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")
        raise