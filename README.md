# Daily IPO Report Emailer

This project automatically fetches IPO data, filters currently open IPOs, evaluates them based on **GMP, Fire Rating, and Subscription**, and sends a daily email report with recommendations.

---

## Features

- **Fetch IPO data** dynamically from your source API.
- **Highlight recommended IPOs** based on the criteria:
  - GMP ≥ 20%
  - 🔥 Fire Rating ≥ 4
  - Subscription ≥ 5×
- **Calculate minimum investment** based on `Price × Lot`.
- **Send HTML email** with:
  - IPO details: Name, GMP, Fire Rating, Price, Lot, IPO Size, Subscription, Open/Close/Listing dates.
  - Recommended badge and subtle row highlighting for suggested IPOs.
- **Automatically bold GMP percentages** and display Fire rating with 🔥 icons.
- Works with **SMTP email** (Gmail or other providers).
- Can be scheduled to run **daily** using **GitHub Actions** or other cloud schedulers.

---

## Requirements

- Python 3.8+
- Libraries (install via `pip install -r requirements.txt`)

---

## Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/aryangoyal1812/Ipo-Bot.git
cd ipo-bot
