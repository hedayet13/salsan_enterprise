# Salsan enterprise Car Dealer (Flask + SQLite)

A clean Flask, with:
- Stock cars
- Delivered cars
- Search & filter
- Contact/inquiry messages stored in DB
- Admin login + dashboard + car/message management
- SQLite database

## Quickstart

```bash
cd salsanenterprise
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1) Initialize the database
flask --app app.py init-db

# 2) Create an admin user (you'll be prompted for username/password)
flask --app app.py create-admin

# 3) (Optional) Seed some demo cars
flask --app app.py seed

# 4) Run the server
flask --app app.py run
# Visit http://127.0.0.1:5000
```

## Environment Variables

- `SECRET_KEY` — Flask session key (set to a strong random string in production)
- `DATABASE_URL` — defaults to `sqlite:///database.db`
- `PER_PAGE` — items per page on `/stock` (default 12)

## Notes

- Upload/hosting of real images is not included; paste any public image URL into the "Image URL" field when adding/editing a car.
- Contact form submissions are stored in the Messages table, accessible in the Admin panel.
- Delivered cars are shown on the "Delivered" page; you can toggle a car's delivered status in the admin list.
- Basic, modern dark UI using vanilla CSS.
