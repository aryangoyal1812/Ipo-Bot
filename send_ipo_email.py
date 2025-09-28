# Build Scraper Module – Fetch & sort IPO data.

# Build Email Sender Module – Simple SMTP function.

# Build Subscription Storage – SQLite/PostgreSQL with basic subscribers table.

# Tie Together in send_ipo_email.py – Fetch → Format → Send.

# Set Cron Jobs – On your local machine first, then deploy to VPS.

# Testing – Use a test email account and small subscriber list.

# Shift to Production Email Service – Migrate to SendGrid or SES to avoid Gmail rate limits

import os
import requests
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import urllib.parse
from datetime import date
import time

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY") 
# === CONFIG ===
BASE_URL = "https://webnodejs.investorgain.com/cloud/report/data-read/331/1/9/2025/2025-26/0/all"

SENDER = os.getenv("SENDER_EMAIL")                       # e.g. youremail@gmail.com
PASSWORD = os.getenv("GMAIL_APP_PASS")                   # Gmail App Password (16 chars)
RECIPIENTS = os.getenv("RECIPIENTS", "")                 # comma-separated emails
RECIPIENTS = [r.strip() for r in RECIPIENTS.split(",") if r.strip()]
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

DISCLAIMER = """
<hr>
<p style="font-size:12px;color:gray;">
Disclaimer: This information is provided for educational purposes only. 
It is sourced from public data on Investorgain. 
Please verify independently before making any investment decisions.
</p>
"""

def clean_html(value):
    return BeautifulSoup(str(value), "html.parser").get_text(separator=" ").strip()

def build_dynamic_url():
    # Use current hour and minute to generate a v param for cache-busting
    now = datetime.now()
    v_param = now.strftime("%H-%M")
    params = {"search": "", "v": v_param}
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"

def fetch_and_filter_open_ipos():
    url = build_dynamic_url()
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()["reportTableData"]

    today = datetime.now().date()
    open_ipos = []
    for item in data:
        try:
            open_date = datetime.strptime(clean_html(item.get("~Srt_Open", "")), "%Y-%m-%d").date()
            close_date = datetime.strptime(clean_html(item.get("~Srt_Close", "")), "%Y-%m-%d").date()
        except ValueError:
            # Skip entries with invalid dates
            continue

        if open_date <= today <= close_date:
            open_ipos.append(item)

    # Sort descending by Close date
    open_ipos.sort(
        key=lambda x: datetime.strptime(clean_html(x.get("~Srt_Close", "")), "%Y-%m-%d"),
        reverse=False
    )
    return open_ipos

def create_email_html(ipos):
    if not ipos:
        return f"<p>No IPOs are currently open.</p>{DISCLAIMER}"

    rows = ""
    for item in ipos:
        name = clean_html(item.get("Name", "--"))
        gmp_raw = clean_html(item.get("GMP", "--"))
        price_str = clean_html(item.get("Price", "0")).replace(",", "")
        lot_str = clean_html(item.get("Lot", "0")).replace(",", "")
        ipo_size = clean_html(item.get("IPO Size", "--"))
        fire_rating_raw = clean_html(item.get("Rating", ""))
        sub = clean_html(item.get("Sub", "--"))
        open_date = clean_html(item.get("Open", "--"))
        close_date = clean_html(item.get("Close", "--"))
        listing = clean_html(item.get("Listing", "--"))

        import re
        # Extract numeric GMP %
        gmp_match = re.search(r"(\d+(\.\d+)?)%", gmp_raw)
        gmp_percent = float(gmp_match.group(1)) if gmp_match else 0
        # Bold the GMP percentage
        gmp = re.sub(r"(\d+(\.\d+)?%)", r"<b>\1</b>", gmp_raw)

        # Count fire emojis (🔥 or &#128293;)
        fire_count = fire_rating_raw.count("🔥") or fire_rating_raw.count("&#128293;")
        fire_display = fire_rating_raw  # keep original fire display

        # Parse subscription as float
        try:
            sub_value = float(sub.lower().replace("x", "").strip())
        except:
            sub_value = 0

        # Calculate minimum investment
        try:
            price = float(price_str)
            lot = int(lot_str)
            min_investment = f"₹{int(price * lot):,}"
        except ValueError:
            price = 0
            min_investment = "--"

        # Highlight/recommended condition
        highlight = gmp_percent >= 20 and fire_count >= 4 and sub_value >= 5
        highlight_class = "highlight" if highlight else ""
        recommended_badge = '<span style="color:white;background-color:#FF5733;padding:2px 5px;border-radius:4px;margin-left:5px;font-size:0.8em;">Recommended</span>' if highlight else ""

        rows += f"""
        <tr class="{highlight_class}">
            <td>{name} {recommended_badge}</td>
            <td>{gmp}</td>
            <td>{fire_display}</td>
            <td>₹{price_str}</td>
            <td>{ipo_size}</td>
            <td>{lot_str}</td>
            <td>{sub}</td>
            <td>{min_investment}</td>
            <td>{open_date}</td>
            <td>{close_date}</td>
            <td>{listing}</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
      <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:nth-child(even) {{background-color: #f9f9f9;}}
        .highlight {{
            background-color: #d8f5d2;
            font-weight: bold;
            border-left: 4px solid #FF5733;
        }}
        .note {{
            margin-top: 20px;
            font-style: italic;
            color: #444;
        }}
      </style>
    </head>
    <body>
      <h2>Currently Open IPOs</h2>
      <p>Here are the IPOs open for subscription today:</p>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>GMP</th>
            <th>🔥 Fire Rating(5)</th>
            <th>Price/Share</th>
            <th>IPO Size</th>
            <th>Lot</th>
            <th>Subscription</th>
            <th>Min Investment</th>
            <th>Open</th>
            <th>Close</th>
            <th>Listing</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
      <p class="note">
        ✨ <b>Recommended badge</b> indicates IPOs meeting all three criteria: <b>GMP ≥ 20%</b>,
        <b>🔥 Fire Rating ≥ 4</b>, and <b>Subscription ≥ 5×</b>. These IPOs may deserve closer attention, 
        but always conduct your own research before investing.
      </p>
      {DISCLAIMER}
    </body>
    </html>
    """
    return html

def send_email(subject, plain_text, html_content=None, delay=2):
    today = date.today().strftime("%d-%b-%Y")
    subject_with_date = f"{subject} - {today}"

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER, PASSWORD)

            for recipient in RECIPIENTS:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = SENDER
                msg["To"] = recipient

                # Always include plain text
                msg.attach(MIMEText(plain_text, "plain"))

                # Optionally include HTML version
                if html_content:
                    msg.attach(MIMEText(html_content, "html"))

                server.sendmail(SENDER, recipient, msg.as_string())
                print(f"Email sent to {recipient}")
                time.sleep(delay)  # Pause to avoid rate limiting/spam filters

    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    ipos = fetch_and_filter_open_ipos()
    html_body = create_email_html(ipos)
    # print(html_body)  # For debugging
    today_str = datetime.now().strftime("%d-%b-%Y")
    plain_message = "Here is your daily IPO update. Check the attachment or details below."
    send_email(f"Daily IPO Report ({today_str})", plain_message, html_body)
    print(f"Sent email with {len(ipos)} open IPO(s).")
