#todo devilered list done


from datetime import datetime
import click
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app
from urllib.parse import urlencode

from flask import session as flask_session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import uuid
from werkzeug.utils import secure_filename
from models import db, Admin, Car, Message, CarImage


from config import Config

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # ensure upload directory exists
    upload_folder = app.config.get("UPLOAD_FOLDER", "static/uploads/cars")
    abs_upload = upload_folder if os.path.isabs(upload_folder) else os.path.join(app.root_path, upload_folder)
    os.makedirs(abs_upload, exist_ok=True)

    def allowed_file(filename):
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return ext in app.config.get("ALLOWED_EXTENSIONS", {"png","jpg","jpeg","gif","webp"})



    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "admin_login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    @app.route("/")
    def home():
        q = request.args.get("q", "").strip()
        cars_q = Car.query.filter_by(is_delivered=False).order_by(Car.created_at.desc())
        if q:
            like = f"%{q}%"
            cars_q = cars_q.filter(
                (Car.title.ilike(like)) |
                (Car.make.ilike(like)) |
                (Car.model.ilike(like)) |
                (Car.description.ilike(like))
            )
        cars = cars_q.limit(8).all()
        return render_template("index.html", cars=cars, q=q)

    @app.route("/stock")
    def stock():
        query = Car.query.filter_by(is_delivered=False)

        # Filters
        q = request.args.get("q", "").strip()
        make = request.args.get("make", "").strip()
        model = request.args.get("model", "").strip()
        fuel = request.args.get("fuel", "").strip()
        trans = request.args.get("transmission", "").strip()
        body = request.args.get("body", "").strip()
        min_year = request.args.get("min_year", type=int)
        max_year = request.args.get("max_year", type=int)
        min_price = request.args.get("min_price", type=int)
        max_price = request.args.get("max_price", type=int)
        sort = request.args.get("sort", "newest")

        if q:
            like = f"%{q}%"
            query = query.filter(
                (Car.title.ilike(like)) |
                (Car.make.ilike(like)) |
                (Car.model.ilike(like)) |
                (Car.description.ilike(like))
            )
        if make: query = query.filter(Car.make.ilike(make))
        if model: query = query.filter(Car.model.ilike(model))
        if fuel: query = query.filter(Car.fuel_type.ilike(fuel))
        if trans: query = query.filter(Car.transmission.ilike(trans))
        if body: query = query.filter(Car.body_type.ilike(body))
        if min_year: query = query.filter(Car.year >= min_year)
        if max_year: query = query.filter(Car.year <= max_year)
        if min_price is not None: query = query.filter(Car.price >= min_price)
        if max_price is not None: query = query.filter(Car.price <= max_price)

        if sort == "price_asc":
            query = query.order_by(Car.price.asc())
        elif sort == "price_desc":
            query = query.order_by(Car.price.desc())
        elif sort == "year_desc":
            query = query.order_by(Car.year.desc(), Car.created_at.desc())
        else:
            query = query.order_by(Car.created_at.desc())

        page = request.args.get("page", 1, type=int)
        per_page = int(request.args.get("per_page", current_app.config.get("PER_PAGE", 12)))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        cars = pagination.items

        return render_template("stock.html", cars=cars, pagination=pagination, params=request.args)

    @app.route("/delivered")
    def delivered():
        cars = Car.query.filter_by(is_delivered=True).order_by(Car.created_at.desc()).all()
        return render_template("delivered.html", cars=cars)

    @app.route("/car/<int:car_id>")
    def car_detail(car_id):
        car = Car.query.get_or_404(car_id)
        return render_template("car_detail.html", car=car)

    @app.post("/inquire/<int:car_id>")
    def inquire(car_id):
        car = Car.query.get_or_404(car_id)
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        body = request.form.get("message", "").strip()
        subject = f"Inquiry about {car.title} (ID {car.id})"
        if not name or not body:
            flash("Please provide your name and message.", "warning")
            return redirect(url_for("car_detail", car_id=car.id))
        msg = Message(name=name, email=email, phone=phone, subject=subject, body=body)
        db.session.add(msg)
        # Replace image if new file uploaded
        file = request.files.get('image_file')
        if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique = f"{uuid.uuid4().hex}_{filename}"
                upload_folder = app.config.get("UPLOAD_FOLDER", "static/uploads/cars")
                abs_upload = upload_folder if os.path.isabs(upload_folder) else os.path.join(app.root_path, upload_folder)
                file.save(os.path.join(abs_upload, unique))
                static_root = os.path.join(app.root_path, 'static')
                rel_to_static = os.path.relpath(os.path.join(abs_upload, unique), static_root)
                car.image_url = url_for('static', filename=rel_to_static.replace('\\','/'))
        db.session.commit()
        flash("Thanks! Your inquiry has been received. We'll get back to you.", "success")
        return redirect(url_for("car_detail", car_id=car.id))

    @app.post("/contact")
    def contact():
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip() or "General Inquiry"
        body = request.form.get("message", "").strip()
        if not name or not body:
            flash("Please provide your name and message.", "warning")
            return redirect(request.referrer or url_for("home"))
        msg = Message(name=name, email=email, phone=phone, subject=subject, body=body)
        db.session.add(msg)
        db.session.commit()
        flash("Thanks! Your message has been sent.", "success")
        return redirect(request.referrer or url_for("home"))

    # ------------------- Admin --------------------
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            admin = Admin.query.filter_by(username=username).first()
            if admin and admin.check_password(password):
                login_user(admin)
                flash("Welcome back!", "success")
                return redirect(url_for("admin_dashboard"))
            flash("Invalid credentials.", "danger")
        return render_template("admin/login.html")

    @app.route("/admin/logout")
    @login_required
    def admin_logout():
        logout_user()
        flash("Logged out.", "info")
        return redirect(url_for("admin_login"))

    @app.route("/admin")
    @login_required
    def admin_dashboard():
        stock_count = Car.query.filter_by(is_delivered=False).count()
        delivered_count = Car.query.filter_by(is_delivered=True).count()
        message_count = Message.query.count()
        latest_msgs = Message.query.order_by(Message.created_at.desc()).limit(5).all()
        latest_cars = Car.query.order_by(Car.created_at.desc()).limit(5).all()
        return render_template("admin/dashboard.html",
                               stock_count=stock_count, delivered_count=delivered_count,
                               message_count=message_count, latest_msgs=latest_msgs,
                               latest_cars=latest_cars)

    @app.route("/admin/cars")
    @login_required
    def admin_cars():
        cars = Car.query.order_by(Car.created_at.desc()).all()
        return render_template("admin/cars_list.html", cars=cars)

    @app.route("/admin/cars/new", methods=["GET", "POST"])
    @login_required
    def admin_cars_new():
        if request.method == "POST":
            car = Car(
                title=request.form.get("title"),
                make=request.form.get("make"),
                model=request.form.get("model"),
                year=request.form.get("year", type=int),
                price=request.form.get("price", type=int),
                mileage_km=request.form.get("mileage_km", type=int),
                fuel_type=request.form.get("fuel_type"),
                transmission=request.form.get("transmission"),
                body_type=request.form.get("body_type"),
                color=request.form.get("color"),
                location=request.form.get("location"),
                description=request.form.get("description"),
                image_url = url_for('static', filename='img/placeholder.svg')
            )
            # Handle main image upload
            # Save multiple images and set cover if not set
            new_files = []
            for i in range(1, 6):
                f = request.files.get(f'image_file{i}')
                if f and f.filename and allowed_file(f.filename):
                    new_files.append(f)

            # Save files (limit 5 total for a new car)
            added_urls = []
            for idx, file in enumerate(new_files[:5]):
                filename = secure_filename(file.filename)
                unique = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(abs_upload, unique))
                static_root = os.path.join(app.root_path, 'static')
                rel_to_static = os.path.relpath(os.path.join(abs_upload, unique), static_root).replace(os.sep, '/')
                added_urls.append(url_for('static', filename=rel_to_static))

            # Create CarImage rows with sort order
            for order, url in enumerate(added_urls):
                db.session.add(CarImage(car=car, url=url, sort_order=order))

            # Set cover if not set or placeholder
            if added_urls and (not car.image_url or 'placeholder.svg' in car.image_url):
                car.image_url = added_urls[0]


            db.session.add(car)
            db.session.commit()
            flash("Car added.", "success")
            return redirect(url_for("admin_cars"))
        return render_template("admin/cars_form.html", car=None)

    @app.route("/admin/cars/<int:car_id>/edit", methods=["GET", "POST"])
    @login_required
    def admin_cars_edit(car_id):
        car = Car.query.get_or_404(car_id)
        if request.method == "POST":
            car.title = request.form.get("title")
            car.make = request.form.get("make")
            car.model = request.form.get("model")
            car.year = request.form.get("year", type=int)
            car.price = request.form.get("price", type=int)
            car.mileage_km = request.form.get("mileage_km", type=int)
            car.fuel_type = request.form.get("fuel_type")
            car.transmission = request.form.get("transmission")
            car.body_type = request.form.get("body_type")
            car.color = request.form.get("color")
            car.location = request.form.get("location")
            car.description = request.form.get("description")
            # keep existing cover image if none uploaded
            car.image_url = car.image_url

            # Gather up to 5 new files
            incoming = []
            for i in range(1, 6):
                f = request.files.get(f'image_file{i}')
                if f and f.filename and allowed_file(f.filename):
                    incoming.append(f)

            # Enforce maximum 5 total images PER CAR
            current_count = len(car.images)
            room = max(0, 5 - current_count)
            to_save = incoming[:room]
            if incoming and room == 0:
                flash("This car already has the maximum of 5 images.", "warning")
            elif len(incoming) > room:
                flash(f"Only {room} more image(s) allowed (max 5 total).", "warning")

            added_urls = []
            for f in to_save:
                filename = secure_filename(f.filename)
                unique = f"{uuid.uuid4().hex}_{filename}"
                f.save(os.path.join(abs_upload, unique))
                static_root = os.path.join(app.root_path, 'static')
                rel_to_static = os.path.relpath(os.path.join(abs_upload, unique), static_root).replace(os.sep, '/')
                added_urls.append(url_for('static', filename=rel_to_static))

            # Append CarImage rows with proper sort order
            next_sort = (car.images[-1].sort_order + 1) if car.images else 0
            for idx, url in enumerate(added_urls):
                db.session.add(CarImage(car=car, url=url, sort_order=next_sort + idx))

            # If cover is empty/placeholder, set to first newly added
            if added_urls and (not car.image_url or 'placeholder.svg' in car.image_url):
                car.image_url = added_urls[0]


            db.session.commit()
            flash("Car updated.", "success")
            return redirect(url_for("admin_cars"))
        return render_template("admin/cars_form.html", car=car)

    
    @app.post("/admin/cars/<int:car_id>/images/<int:image_id>/delete")
    @login_required
    def admin_car_image_delete(car_id, image_id):
        car = Car.query.get_or_404(car_id)
        img = CarImage.query.filter_by(id=image_id, car_id=car.id).first_or_404()

        # try to delete file from disk if it's under /static/
        if img.url and img.url.startswith("/static/"):
            rel = img.url[len("/static/"):]
            abs_path = os.path.join(app.root_path, "static", rel.replace("/", os.sep))
            try:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
            except Exception:
                pass

        db.session.delete(img)
        db.session.commit()
        flash("Image deleted.", "info")
        return redirect(url_for("admin_cars_edit", car_id=car.id))


    @app.route("/admin/cars/<int:car_id>/delete", methods=["POST"])
    @login_required
    def admin_cars_delete(car_id):
        car = Car.query.get_or_404(car_id)
        db.session.delete(car)
        db.session.commit()
        flash("Car deleted.", "info")
        return redirect(url_for("admin_cars"))

    @app.post("/admin/cars/<int:car_id>/toggle-delivered")
    @login_required
    def admin_cars_toggle_delivered(car_id):
        car = Car.query.get_or_404(car_id)
        car.is_delivered = not car.is_delivered
        db.session.commit()
        flash("Delivery status updated.", "success")
        return redirect(url_for("admin_cars"))

    @app.route("/admin/messages")
    @login_required
    def admin_messages():
        msgs = Message.query.order_by(Message.created_at.desc()).all()
        return render_template("admin/messages.html", messages=msgs)

    @app.post("/admin/messages/<int:msg_id>/toggle-read")
    @login_required
    def admin_messages_toggle_read(msg_id):
        msg = Message.query.get_or_404(msg_id)
        msg.is_read = not msg.is_read
        db.session.commit()
        return redirect(url_for("admin_messages"))

    @app.post("/admin/messages/<int:msg_id>/delete")
    @login_required
    def admin_messages_delete(msg_id):
        msg = Message.query.get_or_404(msg_id)
        db.session.delete(msg)
        db.session.commit()
        flash("Message deleted.", "info")
        return redirect(url_for("admin_messages"))

    # --------------- Utilities / API ---------------
    @app.get("/api/makes")
    def api_makes():
        makes = [m[0] for m in db.session.query(Car.make).distinct().all() if m[0]]
        return jsonify(sorted(makes))

    @app.get("/api/models")
    def api_models():
        models = [m[0] for m in db.session.query(Car.model).distinct().all() if m[0]]
        return jsonify(sorted(models))

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "time": datetime.utcnow().isoformat()}

    # CLI to init DB and create admin
    @app.cli.command("init-db")
    def init_db_cmd():
        with app.app_context():
            db.create_all()
            click.echo("Database initialized.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin_cmd(username, password):
        with app.app_context():
            if Admin.query.filter_by(username=username).first():
                click.echo("User already exists.")
                return
            admin = Admin(username=username)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            click.echo("Admin created.")

    @app.cli.command("seed")
    def seed_cmd():
        with app.app_context():
            if Car.query.count() > 0:
                click.echo("Cars already exist, skipping seed.")
                return
            sample = [
                Car(title="Toyota Corolla X 2018", make="Toyota", model="Corolla X", year=2018, price=1650000,
                    mileage_km=52000, fuel_type="Petrol", transmission="Automatic", body_type="Sedan", color="White",
                    location="Dhaka", description="Clean import. Push start, reverse camera, fresh tyres.",
                    image_url="/static/img/placeholder.svg"),
                Car(title="Honda Vezel 2020", make="Honda", model="Vezel", year=2020, price=2850000,
                    mileage_km=33000, fuel_type="Hybrid", transmission="Automatic", body_type="SUV", color="Blue",
                    location="Dhaka", description="Z package with sensing.", image_url="/static/img/placeholder.svg"),
                Car(title="Mazda Axela 2017", make="Mazda", model="Axela", year=2017, price=1550000,
                    mileage_km=61000, fuel_type="Petrol", transmission="Automatic", body_type="Hatchback", color="Red",
                    location="Chittagong", description="Bose audio, heads-up display.", image_url="/static/img/placeholder.svg"),
            ]
            for c in sample:
                db.session.add(c)
            db.session.commit()
            click.echo("Seeded cars.")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
