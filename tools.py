import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool
from database import SessionLocal
from models import Customer, Appointment


def send_notification_email(to_email: str, customer_name: str, appointment_title: str, start_time_str: str):

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        return "SMTP ayarları eksik olduğu için mail gönderilemedi."

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = f"Randevu Hatırlatması: {appointment_title}"

    body = f"Merhaba {customer_name},\n\nSizinle '{start_time_str}' tarihinde bir randevu oluşturulmuştur.\n\nİyi günler dileriz."
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()

        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        return "E-posta başarıyla gönderildi."
    except Exception as e:
        return f"E-posta gönderimi sırasında hata oluştu: {str(e)}"


@tool
def add_customer(name: str, email: Optional[str] = None, phone: Optional[str] = None, company: Optional[str] = None,
                 notes: Optional[str] = None) -> str:
    db = SessionLocal()
    try:
        customer = Customer(name=name, email=email, phone=phone, company=company, notes=notes)
        db.add(customer)
        db.commit()
        return f"Müşteri başarıyla eklendi: {name} (ID: {customer.id})"
    except Exception as e:
        db.rollback()
        return f"Müşteri eklenirken hata oluştu: {str(e)}"
    finally:
        db.close()


@tool
def create_appointment(title: str, start_time_str: str, customer_name: Optional[str] = None,
                       description: Optional[str] = None) -> str:
    db = SessionLocal()
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        customer = None

        if customer_name:
            # İsme göre müşteriyi buluyoruz
            customer = db.query(Customer).filter(Customer.name.ilike(f"%{customer_name}%")).first()

        appointment = Appointment(
            customer_id=customer.id if customer else None,
            title=title,
            start_time=start_time,
            description=description
        )
        db.add(appointment)
        db.commit()

        base_status = f"Randevu başarıyla oluşturuldu: {title} - Zaman: {start_time_str}."

        # E-posta Gönderim Kontrolü
        send_email_env = os.getenv("SEND_EMAIL", "false").lower() == "true"

        if send_email_env:
            if customer and customer.email:
                mail_status = send_notification_email(customer.email, customer.name, title, start_time_str)
                return f"{base_status} {mail_status}"
            else:
                # E-posta gönderimi açık ama müşterinin mail adresi yoksa agent'a bu durumu bildiriyoruz
                return f"{base_status} UYARI: E-posta bildirimi gönderme ayarı açık ancak bu müşterinin sistemde kayıtlı bir e-posta adresi bulunamadı. Kullanıcıya kendisinin manuel olarak mesaj atması gerektiğini hatırlat."

        return base_status

    except Exception as e:
        db.rollback()
        return f"Randevu oluşturulurken hata: {str(e)}"
    finally:
        db.close()


@tool
def list_appointments() -> str:
    """Gelecek tüm randevuların ve takvim etkinliklerinin listesini getirir."""
    db = SessionLocal()
    try:
        apps = db.query(Appointment).order_by(Appointment.start_time.asc()).all()
        if not apps:
            return "Kayıtlı randevu bulunamadı."
        result = "Mevcut Randevular:\n"
        for app in apps:
            cust_name = app.customer.name if app.customer else "Bilinmeyen Müşteri"
            result += f"- {app.title} | Müşteri: {cust_name} | Zaman: {app.start_time} | Açıklama: {app.description}\n"
        return result
    except Exception as e:
        return f"Randevular listelenirken hata: {str(e)}"
    finally:
        db.close()



get_tools = [add_customer, create_appointment, list_appointments]