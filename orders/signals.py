from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order
from accounts.models import User

@receiver(post_save, sender=Order)
def notify_admin_on_paid_order(sender, instance, created, **kwargs):
    # Only notify if order status changed to 'paid' (not on creation)
    if not created and instance.status == 'paid':
        # Check if this is a transition from pending to paid
        # For simplicity, we assume the signal is called after save with updated status.
        # We'll also send email to all admin users.
        admins = User.objects.filter(role='admin')
        for admin in admins:
            # In-app notification: could be stored in a Notification model, but we'll just send email
            subject = f"New Order #{instance.id} has been paid"
            message = f"Order #{instance.id} from {instance.user.username} has been paid. Total amount: KSh {instance.total_amount}. Please check the admin dashboard."
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin.email], fail_silently=True)
        # Also print to console for development
        print(f"NOTIFICATION: Order {instance.id} paid by {instance.user.username}")