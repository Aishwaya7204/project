from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-demo-secret"
DB_PATH = Path(__file__).with_name("marketplace.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            skills TEXT DEFAULT '',
            portfolio TEXT DEFAULT '',
            niche TEXT DEFAULT '',
            budget_min INTEGER DEFAULT 0,
            budget_max INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pending'
        );
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            budget INTEGER NOT NULL,
            deadline TEXT DEFAULT '',
            status TEXT DEFAULT 'Open'
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            campaign_id INTEGER NOT NULL,
            ai_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(creator_id, campaign_id),
            FOREIGN KEY(creator_id) REFERENCES users(id),
            FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
        );
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            work_link TEXT NOT NULL,
            status TEXT DEFAULT 'Submitted',
            FOREIGN KEY(application_id) REFERENCES applications(id)
        );
        """)
        # Add demo campaigns once, so the app has something to explore.
        count = db.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO campaigns (brand_name,title,category,description,budget,deadline) VALUES (?,?,?,?,?,?)",
                [
                    ("StyleNest", "AI Fashion Reel", "Fashion", "Create a short AI-assisted fashion promotional reel.", 5000, "2026-11-15"),
                    ("GlowCare", "Skincare Product Visuals", "Beauty", "Create product visuals for a skincare social media campaign.", 3500, "2026-11-20"),
                    ("ByteBrew", "Tech Product Explainer", "Technology", "Create a clear, engaging short explainer video for a tech product.", 6000, "2026-11-25"),
                ]
            )

def current_user():
    if "user_id" not in session:
        return None
    with get_db() as db:
        return db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()

def require_role(role):
    user = current_user()
    if not user or user["role"] != role:
        flash("Please log in with the correct role first.", "error")
        return False
    return True

def score_creator(creator, campaign):
    """Simple explainable matching score for the hackathon demo (not an external AI model)."""
    skills = (creator["skills"] or "").lower()
    niche = (creator["niche"] or "").lower()
    category = campaign["category"].lower()
    score = 40
    reasons = []
    if category in niche:
        score += 30
        reasons.append("niche matches campaign")
    if any(word in skills for word in ["ai", "video", "design", "image", "content", category]):
        score += 20
        reasons.append("relevant skills found")
    if creator["budget_min"] <= campaign["budget"] <= max(creator["budget_max"], creator["budget_min"]):
        score += 10
        reasons.append("budget fits creator range")
    return min(score, 100), (", ".join(reasons) if reasons else "general profile match")

@app.route("/")
def index():
    with get_db() as db:
        campaigns = db.execute("SELECT * FROM campaigns WHERE status='Open' ORDER BY id DESC").fetchall()
    return render_template("index.html", campaigns=campaigns, user=current_user())

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        if role not in ("creator", "brand", "agency"):
            flash("Choose a valid account type.", "error")
            return redirect(url_for("register"))
        skills = request.form.get("skills", "").strip()
        portfolio = request.form.get("portfolio", "").strip()
        niche = request.form.get("niche", "").strip()
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO users (name,email,password,role,skills,portfolio,niche,budget_min,budget_max) VALUES (?,?,?,?,?,?,?,?,?)",
                    (name, email, password, role, skills, portfolio, niche,
                     int(request.form.get("budget_min") or 0), int(request.form.get("budget_max") or 0))
                )
            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "error")
    return render_template("register.html", user=current_user())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        # Admin demo credentials are listed in README.
        if role == "admin" and email == "admin@marketplace.demo" and password == "admin123":
            session["user_id"] = -1
            session["role"] = "admin"
            flash("Logged in as demo admin.", "success")
            return redirect(url_for("admin_dashboard"))
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email=? AND password=? AND role=?", (email, password, role)).fetchone()
        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Welcome back!", "success")
            if user["role"] == "creator":
                return redirect(url_for("creator_dashboard"))
            return redirect(url_for("brand_dashboard"))
        flash("Login details are incorrect.", "error")
    return render_template("login.html", user=current_user())

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("index"))

@app.route("/campaign/<int:campaign_id>")
def campaign_detail(campaign_id):
    with get_db() as db:
        campaign = db.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    if not campaign:
        flash("Campaign not found.", "error")
        return redirect(url_for("index"))
    return render_template("campaign.html", campaign=campaign, user=current_user())

@app.route("/apply/<int:campaign_id>", methods=["POST"])
def apply(campaign_id):
    user = current_user()
    if not user or user["role"] != "creator":
        flash("Please log in as a creator to apply.", "error")
        return redirect(url_for("login"))
    with get_db() as db:
        campaign = db.execute("SELECT * FROM campaigns WHERE id=? AND status='Open'", (campaign_id,)).fetchone()
        if not campaign:
            flash("This campaign is not open.", "error")
            return redirect(url_for("index"))
        score, reason = score_creator(user, campaign)
        try:
            db.execute("INSERT INTO applications (creator_id,campaign_id,ai_score) VALUES (?,?,?)",
                       (user["id"], campaign_id, score))
            flash(f"Application submitted. AI match score: {score}%. Admin will make the final decision.", "success")
        except sqlite3.IntegrityError:
            flash("You have already applied to this campaign.", "error")
    return redirect(url_for("creator_dashboard"))

@app.route("/creator")
def creator_dashboard():
    user = current_user()
    if not user or user["role"] != "creator":
        flash("Please log in as a creator.", "error")
        return redirect(url_for("login"))
    with get_db() as db:
        applications = db.execute("""
            SELECT a.*, c.title, c.brand_name, c.category, c.budget
            FROM applications a JOIN campaigns c ON c.id=a.campaign_id
            WHERE a.creator_id=? ORDER BY a.id DESC
        """, (user["id"],)).fetchall()
        campaigns = db.execute("SELECT * FROM campaigns WHERE status='Open' ORDER BY id DESC").fetchall()
    return render_template("creator_dashboard.html", user=user, applications=applications, campaigns=campaigns)

@app.route("/brand", methods=["GET", "POST"])
def brand_dashboard():
    user = current_user()
    if not user or user["role"] not in ("brand", "agency"):
        flash("Please log in as a brand or agency.", "error")
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            with get_db() as db:
                db.execute("""INSERT INTO campaigns (brand_name,title,category,description,budget,deadline)
                              VALUES (?,?,?,?,?,?)""",
                           (request.form["brand_name"].strip(), request.form["title"].strip(),
                            request.form["category"].strip(), request.form["description"].strip(),
                            int(request.form["budget"]), request.form.get("deadline", "")))
            flash("Campaign created successfully.", "success")
            return redirect(url_for("brand_dashboard"))
        except (ValueError, KeyError):
            flash("Please complete all campaign fields correctly.", "error")
    with get_db() as db:
        campaigns = db.execute("SELECT * FROM campaigns ORDER BY id DESC").fetchall()
        applications = db.execute("""
            SELECT a.*, u.name AS creator_name, u.skills, u.niche, u.portfolio,
                   c.title, c.brand_name, c.category, c.budget
            FROM applications a JOIN users u ON u.id=a.creator_id
            JOIN campaigns c ON c.id=a.campaign_id ORDER BY a.ai_score DESC
        """).fetchall()
    return render_template("brand_dashboard.html", user=user, campaigns=campaigns, applications=applications)

@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Please log in as admin.", "error")
        return redirect(url_for("login"))
    with get_db() as db:
        users = db.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
        applications = db.execute("""
            SELECT a.*, u.name AS creator_name, u.email, u.skills, u.niche, u.portfolio,
                   c.title, c.brand_name, c.category, c.budget
            FROM applications a JOIN users u ON u.id=a.creator_id
            JOIN campaigns c ON c.id=a.campaign_id ORDER BY a.ai_score DESC
        """).fetchall()
    return render_template("admin_dashboard.html", users=users, applications=applications)

@app.route("/admin/user/<int:user_id>/<action>", methods=["POST"])
def admin_user_action(user_id, action):
    if session.get("role") != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("login"))
    if action not in ("approve", "reject"):
        return redirect(url_for("admin_dashboard"))
    status = "Approved" if action == "approve" else "Rejected"
    with get_db() as db:
        db.execute("UPDATE users SET status=? WHERE id=?", (status, user_id))
    flash(f"User {status.lower()}.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/application/<int:application_id>/<action>", methods=["POST"])
def admin_application_action(application_id, action):
    if session.get("role") != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("login"))
    mapping = {"approve": "Admin Approved", "reject": "Rejected"}
    if action not in mapping:
        return redirect(url_for("admin_dashboard"))
    with get_db() as db:
        db.execute("UPDATE applications SET status=? WHERE id=?", (mapping[action], application_id))
    flash(f"Application {mapping[action].lower()}.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/submit-work/<int:application_id>", methods=["POST"])
def submit_work(application_id):
    user = current_user()
    if not user or user["role"] != "creator":
        flash("Creator login required.", "error")
        return redirect(url_for("login"))
    link = request.form.get("work_link", "").strip()
    if not link:
        flash("Enter a link to your completed work.", "error")
        return redirect(url_for("creator_dashboard"))
    with get_db() as db:
        app_row = db.execute("SELECT * FROM applications WHERE id=? AND creator_id=?", (application_id, user["id"])).fetchone()
        if not app_row or app_row["status"] != "Admin Approved":
            flash("Work can be submitted after admin approval.", "error")
            return redirect(url_for("creator_dashboard"))
        db.execute("INSERT INTO submissions (application_id,work_link) VALUES (?,?)", (application_id, link))
        db.execute("UPDATE applications SET status='Work Submitted' WHERE id=?", (application_id,))
    flash("Work submitted for brand review. Payment is not processed automatically in this demo.", "success")
    return redirect(url_for("creator_dashboard"))

@app.route("/brand/complete/<int:application_id>", methods=["POST"])
def brand_complete(application_id):
    user = current_user()
    if not user or user["role"] not in ("brand", "agency"):
        flash("Brand or agency login required.", "error")
        return redirect(url_for("login"))
    with get_db() as db:
        row = db.execute("SELECT * FROM applications WHERE id=?", (application_id,)).fetchone()
        if not row or row["status"] != "Work Submitted":
            flash("Work must be submitted before approval.", "error")
        else:
            db.execute("UPDATE applications SET status='Brand Approved - Payment Pending' WHERE id=?", (application_id,))
            flash("Work approved. Admin can now verify and update payment status.", "success")
    return redirect(url_for("brand_dashboard"))

@app.route("/admin/payment/<int:application_id>", methods=["POST"])
def admin_payment(application_id):
    if session.get("role") != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("login"))
    with get_db() as db:
        db.execute("UPDATE applications SET status='Paid (Demo)' WHERE id=? AND status='Brand Approved - Payment Pending'", (application_id,))
    flash("Payment marked as paid in demo mode. No real money was transferred.", "success")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
