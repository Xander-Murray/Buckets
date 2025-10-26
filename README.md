# Buckets — Budget with Intent

A fast, keyboard-friendly TUI for envelope-style budgeting. Track accounts, categorize spending, assign funds to **Buckets**, and fire off new records from **Templates** in seconds — even if you only use one checking account.

> **Why Buckets?** Most beginners don’t want ten bank accounts. Buckets gives every dollar a job with **virtual envelopes** and **zero-friction input**, so you budget with **intent**, not friction.

---

## Screenshots

> Replace these placeholders with real images from your repo (e.g., `docs/screens/`).

**Home Page**

![Home page](screenshots/home.png)

**Buckets View**

![Buckets page](screenshots/buckets.png)

---

## Features

- **Accounts**: multiple accounts with running balances
- **Records**: lightning-fast add/edit of expenses & income
- **Buckets**: visually allocate money (virtual envelopes)
- **Templates**: 1–9 hotkeys to add frequent records instantly
- **Insights**: period totals & daily averages at a glance
- **Period Navigation**: compact calendar with week/month/year filters
- **Keyboard-first**: modal forms, focus movement, and hotkeys

---

## Quick Start

### Prereqs

- Python **3.11+**
- A virtualenv or your preferred environment manager

### Install

```bash
git clone https://github.com/Xander-Murray/Buckets.git
cd Buckets
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

### Run

```bash
python -m buckets
```

