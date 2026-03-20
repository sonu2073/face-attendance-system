"""
emailer.py
Send daily attendance email report with Excel attachment.
"""

import smtplib
import os
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import date
from database import db
from modules.exporter import export_daily


def send_daily_report(on_success=None, on_error=None):
    """Send today's attendance report email. Runs in background thread."""
    def _send():
        try:
            host     = db.get_setting("smtp_host", "smtp.gmail.com")
            port     = int(db.get_setting("smtp_port", "587"))
            user     = db.get_setting("smtp_user", "")
            password = db.get_setting("smtp_pass", "")
            to_addr  = db.get_setting("report_to",  "")

            if not all([user, password, to_addr]):
                if on_error:
                    on_error("Email not configured. Go to Settings → Email.")
                return

            # Generate Excel
            xlsx_path = export_daily()

            # Build email
            today   = date.today().isoformat()
            total, present, absent = db.get_dashboard_counts()
            rate    = round(present / total * 100) if total else 0

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📋 Attendance Report — {today}"
            msg["From"]    = user
            msg["To"]      = to_addr

            html = f"""
            <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
              <div style="max-width:520px;margin:auto;background:#fff;border-radius:8px;overflow:hidden;">
                <div style="background:#1A472A;padding:20px;text-align:center;">
                  <h2 style="color:#fff;margin:0;">Face Attendance System</h2>
                  <p style="color:#95D5B2;margin:4px 0 0;">Daily Report — {today}</p>
                </div>
                <div style="padding:24px;">
                  <table width="100%" cellpadding="10" style="border-collapse:collapse;">
                    <tr>
                      <td style="background:#D8F3DC;border-radius:6px;text-align:center;">
                        <div style="font-size:28px;font-weight:bold;color:#1B4332;">{present}</div>
                        <div style="color:#52B788;font-size:12px;">PRESENT</div>
                      </td>
                      <td width="16"></td>
                      <td style="background:#FFE8E8;border-radius:6px;text-align:center;">
                        <div style="font-size:28px;font-weight:bold;color:#7F1D1D;">{absent}</div>
                        <div style="color:#EF4444;font-size:12px;">ABSENT</div>
                      </td>
                      <td width="16"></td>
                      <td style="background:#EFF6FF;border-radius:6px;text-align:center;">
                        <div style="font-size:28px;font-weight:bold;color:#1E3A8A;">{rate}%</div>
                        <div style="color:#3B82F6;font-size:12px;">RATE</div>
                      </td>
                    </tr>
                  </table>
                  <p style="color:#666;font-size:13px;margin-top:20px;">
                    The Excel attendance sheet is attached to this email.
                  </p>
                </div>
                <div style="background:#F9FAFB;padding:12px;text-align:center;">
                  <p style="color:#9CA3AF;font-size:11px;margin:0;">
                    Sent by Face Attendance System
                  </p>
                </div>
              </div>
            </body></html>
            """
            msg.attach(MIMEText(html, "html"))

            # Attach Excel
            with open(xlsx_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f"attachment; filename=attendance_{today}.xlsx")
            msg.attach(part)

            # Send
            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                server.starttls()
                server.login(user, password)
                server.sendmail(user, to_addr, msg.as_string())

            if on_success:
                on_success(f"Report sent to {to_addr}")

        except Exception as e:
            if on_error:
                on_error(str(e))

    threading.Thread(target=_send, daemon=True).start()


def schedule_daily(app_root):
    """
    Check every minute if it's time to send the daily email.
    Call this once after the main window is ready.
    """
    import tkinter as tk
    from datetime import datetime

    def _check():
        send_time = db.get_setting("send_time", "18:00")
        now = datetime.now().strftime("%H:%M")
        if now == send_time:
            to_addr = db.get_setting("report_to", "")
            if to_addr:
                send_daily_report()
        app_root.after(60_000, _check)

    app_root.after(60_000, _check)
