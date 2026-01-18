# Quickstart

## 1) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

## 2) Configure

Edit `config.yaml` with your Apple Reminders CalDAV credentials and confirm the timezone:

```yaml
dashboard:
  timezone: Europe/Istanbul

reminders:
  method: caldav
  username: "<apple_id_email>"
  app_password: "<app_specific_password>"
  caldav_url: "<full CalDAV base or principal URL>"
  list_name: "Reminders"
  max_items: 8
  show_completed: false
```

## 3) Test render

```bash
python3 dashboard.py --test-mode
```

Check `dashboard_preview.png`.

## 4) Run on display

```bash
python3 dashboard.py
```
