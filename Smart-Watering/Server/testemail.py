import smtplib

EMAIL = "wafaq92@gmail.com"
PASSWORD = "nrywnvyaspkyjlaw"

server = smtplib.SMTP(
    "smtp.gmail.com",
    587
)

server.starttls()

server.login(
    EMAIL,
    PASSWORD
)

print("LOGIN SUCCESS")