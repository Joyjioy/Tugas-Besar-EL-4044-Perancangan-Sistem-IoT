import smtplib
from email.mime.text import MIMEText

# Kredensial pengirim dan penerima diimpor dari file konfigurasi
from config import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECEIVER
)

def send_email(subject, body):
    """Mengirim notifikasi email menggunakan server SMTP Gmail."""
    try:
        # Konfigurasi isi (body) dan metadata/header pesan
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        # Inisialisasi koneksi ke server SMTP Gmail (Port 587 standar untuk TLS)
        server = smtplib.SMTP("smtp.gmail.com", 587)

        # Upgrade koneksi menjadi safe (terenkripsi)
        server.starttls()

        # Autentikasi akun dan eksekusi pengiriman pesan
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        # Putuskan koneksi ke server setelah operasi selesai
        server.quit()

        print("Email sent successfully")

    except Exception as e:
        # Error handling
        print("Email error:", e)
