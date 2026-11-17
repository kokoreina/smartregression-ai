"""Gmail SMTP delivery. Tokens exist only in message memory, never diagnostics."""

import smtplib
import ssl
from dataclasses import dataclass, field
from email.message import EmailMessage
from urllib.parse import urlencode

from smartregression.application.auth import MailDeliveryError


@dataclass(frozen=True)
class GmailMailer:
    username: str
    password: str = field(repr=False)
    frontend_origin: str = "http://127.0.0.1:5173"

    def send(self, email: str, purpose: str, token: str) -> None:
        if not self.username or not self.password:
            raise MailDeliveryError()
        page = "verify-email" if purpose == "verify" else "reset-password"
        link = f"{self.frontend_origin}/{page}#" + urlencode({"token": token})
        message = EmailMessage()
        message["From"] = self.username
        message["To"] = email
        message["Subject"] = (
            "SmartRegression - Xac thuc email"
            if purpose == "verify"
            else "SmartRegression - Dat lai mat khau"
        )
        message.set_content(
            "SmartRegression AI\n\n"
            + (
                "Xác thực địa chỉ email (hạn 24 giờ):\n"
                if purpose == "verify"
                else "Đặt lại mật khẩu (hạn 1 giờ):\n"
            )
            + link
            + "\n\nNếu không yêu cầu, bạn có thể bỏ qua email này."
        )
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as client:
                client.ehlo()
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
                client.login(self.username, self.password.replace(" ", ""))
                if client.send_message(message):
                    raise MailDeliveryError()
        except smtplib.SMTPAuthenticationError:
            raise MailDeliveryError("authentication_failed") from None
        except smtplib.SMTPRecipientsRefused:
            raise MailDeliveryError("recipient_rejected") from None
        except OSError:
            raise MailDeliveryError("connection_failed") from None
        except smtplib.SMTPException, ValueError:
            raise MailDeliveryError() from None
