from django.core.mail import send_mail


def send_email(subject, message, from_email, recipient_list):
    """
    Utility function to send an email.
    
    Args:
        subject (str): Email subject line
        message (str): Email body content
        from_email (str): Sender email address
        recipient_list (list): List of recipient email addresses (e.g., ['user@example.com'])
    
    Returns:
        int: Number of successfully delivered messages
    """
    try:
        return send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email: {e}")
        return 0