import logging
import os
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


class EmailUtil:
    def __init__(self, prod: bool = True) -> None:
        logger.info("## Initialisation de EmailUtil (SMTP) ##")
        self.TESTING = getattr(settings, 'TESTING', False)
        logger.info(f"Testing mode: {self.TESTING}")

    def send_generic_email(
        self,
        subject: str,
        content: str,
        to: List[str],
        sender_name: Optional[str] = None,
        sender_email: Optional[str] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send a generic email using SMTP via Django's EmailMessage.
        """
        logger.info("## Envoi de l'email générique via SMTP ##")

        # Fallback to defaults from settings if not provided
        default_sender = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@e-hooyia.com')
        from_email = sender_email or default_sender
        
        # If sender_name is provided, format as "Name <email@example.com>"
        if sender_name and sender_email:
            from_email = f"{sender_name} <{sender_email}>"
        elif sender_name and not sender_email:
            from_email = f"{sender_name} <{default_sender}>"

        if self.TESTING:
            subject = f"[TEST] {subject}"
            logger.info(
                f"*** MODE TEST EMAIL ***\nSubject: {subject}\nTo: {to}\nBCC: {bcc}\nFrom: {from_email}"
            )
            return True

        try:
            email = EmailMessage(
                subject=subject,
                body=content,
                from_email=from_email,
                to=to,
                bcc=bcc,
            )
            email.content_subtype = "html"  # Main content is now text/html
            email.send()
            logger.info(f"✅ Email sent successfully via SMTP to {to}")
            return True

        except Exception as e:
            logger.error(f"❌ SMTP Error: {e}")
            return False

        except Exception as ex:
            logger.error(f"❌ Unexpected error sending email: {ex}")
            return False

    def send_email_with_template(
        self,
        template: str,
        context: Dict[str, Any],
        receivers: List[str],
        subject: str,
        bcc: Optional[List[str]] = None,
        request=None
    ) -> bool:
        """
        Send email with template using SMTP.
        """
        logger.info(f"Rendering template {template} for email")

        context["subject"] = subject
        
        # Build site URL
        site_url = getattr(settings, 'SITE_URL', '')
        if not site_url.startswith('http'):
            site_url = f"https://{site_url}" if not site_url.startswith('localhost') else f"http://{site_url}"
        
        context["site_url"] = site_url
        context["site_name"] = getattr(settings, 'SITE_NAME', 'HooYia')
        
        
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        
        if static_url.startswith('http'):
            logo_url = f"{static_url}assets/images/logo/coloredLogo.png"
        else:
            logo_url = f"{site_url.rstrip('/')}{static_url}assets/images/logo/coloredLogo.png"
        
        context["logo_url"] = logo_url
        logger.info(f"Logo URL: {logo_url}")

        try:
            body = render_to_string(
                template_name=template,
                context=context,
            )
            sent = self.send_generic_email(
                subject=subject,
                content=body,
                to=receivers,
                bcc=bcc,
            )
            if sent:
                logger.info(f"Email sent successfully to {len(receivers)} recipients")
                return True
            return False
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return False


email_util = EmailUtil()
