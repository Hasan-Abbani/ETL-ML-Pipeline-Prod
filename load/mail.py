import smtplib
from email.message import EmailMessage
from pathlib import Path


class EmailReportSender:
    def __init__(self, sender_email: str, app_password: str):
        self.sender_email = sender_email
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_report(
        self,
        receiver_email: str,
        subject: str,
        body: str,
        attachment_paths=None
    ):
        msg = EmailMessage()
        msg["From"] = self.sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.set_content(body)

        if attachment_paths:
            for attachment_path in attachment_paths:
                file_path = Path(attachment_path)

                if not file_path.exists():
                    print(f"Skipping missing attachment: {file_path}")
                    continue

                with open(file_path, "rb") as file:
                    file_data = file.read()

                msg.add_attachment(
                    file_data,
                    maintype="application",
                    subtype="octet-stream",
                    filename=file_path.name
                )

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.app_password)
            server.send_message(msg)

        print("Email sent successfully.")