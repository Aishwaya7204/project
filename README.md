# AI Creator–Brand Marketplace (ByteXL-friendly starter project)

A beginner-friendly Flask web project for the HackXLerate AI Content Creator Marketplace challenge.

## Features
- Public campaign/brand discovery before login
- Creator, brand, agency and admin roles
- Creator profile, skills, niche and portfolio link
- Brands/agencies can post campaigns
- Explainable rule-based AI-style matching score (demo)
- AI gives recommendations; admin approves/rejects applications
- Work submission link and brand approval workflow
- Demo payment status (does not transfer real money)

## Requirements
- Python 3.10 or newer
- VS Code or ByteXL Python environment
- Internet only for installing Flask

## Run locally
1. Extract the ZIP.
2. Open the extracted `AI_Creator_Brand_Marketplace` folder in VS Code/ByteXL.
3. Open Terminal in that folder.
4. Run:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
5. Open the local URL shown in the terminal, usually `http://127.0.0.1:5000`.

The database `marketplace.db` is created automatically when the app starts.

## Demo admin login
- Role: Admin
- Email: `admin@marketplace.demo`
- Password: `admin123`

## Demo walkthrough
1. Open the home page and browse the sample campaigns without logging in.
2. Register a Creator account. Add skills like `AI video, design, content` and niche like `Fashion`.
3. Log in as Creator, open a campaign and click Apply.
4. Log out. Register/login as a Brand or Agency and create a campaign.
5. Log in as Admin using the demo credentials.
6. Review the AI match score and click Approve or Reject.
7. Log back in as the creator and submit a work URL after approval.
8. Log in as the brand/agency and approve submitted work.
9. Log in as Admin and mark payment as paid in demo mode.

## Important demo limitations
- This starter uses SQLite to make setup easy. It can later be changed to MongoDB if your ByteXL environment requires MongoDB.
- Passwords are stored as plain text for classroom demonstration only. Do not deploy this version with real user data; use password hashing and proper secret management before production.
- Match scores are a simple transparent rule-based demonstration, not a trained AI model.
- Payment is simulated. No real money is transferred.
- Admin approval of an account and approval of an individual campaign application are separate steps.

## Suggested project explanation for viva
“Our platform connects AI content creators with brands and agencies. Creators can explore campaigns before logging in. When they apply, the matching engine checks niche, skills and budget fit and generates a recommendation score. The admin reviews the recommendation and makes the final decision. After the creator submits the work and the brand approves it, the admin updates the demo payment status.”
