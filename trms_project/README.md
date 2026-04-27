# Training & Resource Management System

TRMS is a role-based Django application for internal training operations, daily work tracking, resource occupancy management, batch scheduling, and monthly reporting.

## Included modules

- `accounts`: custom user model, roles, circles, trainer profiles, authentication
- `dashboard`: admin, manager, trainer, and circle lead dashboards
- `tasks`: daily tracker, file uploads, batches, holidays, calendar support
- `reports`: monthly CSV and Excel exports powered by pandas

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Create migrations and migrate:
   `python manage.py makemigrations accounts tasks reports dashboard`
   `python manage.py migrate`
4. Seed sample data:
   `python manage.py seed_trms`
5. Start the server:
   `python manage.py runserver`

Open `http://127.0.0.1:8000/accounts/login/`

## Sample credentials

- Admin: `admin` / `admin12345`
- Manager: `manager1` / `manager12345`
- Circle Lead: `circlelead1` / `circle12345`
- Trainer: `trainer1` / `trainer12345`

## Notes

- Uploaded trainer files are stored in `media/uploads/`
- The monthly report uses a base capacity of `160` hours
- SQLite is configured by default and can be swapped to PostgreSQL in `trms_project/settings.py`

## AWS Elastic Beanstalk deployment

This project is now prepared for AWS Elastic Beanstalk with:

- `.ebextensions/01_django.config`
- `Procfile`
- production-ready static serving through WhiteNoise
- environment-variable driven Django settings
- automatic support for Amazon RDS environment variables

### Before deploy

1. Install the EB CLI on your machine.
2. From the project root, install dependencies:
   `pip install -r requirements.txt`
3. Create an admin user or use the bootstrap flow after deploy.
4. Decide whether you want:
   - SQLite for quick testing
   - PostgreSQL on Amazon RDS for production

### Recommended AWS environment variables

Set these in Elastic Beanstalk:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS=<your-eb-domain>`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-eb-domain>`
- `DJANGO_SECURE_SSL_REDIRECT=true`

If you attach an RDS PostgreSQL database through Elastic Beanstalk, Django automatically reads:

- `RDS_DB_NAME`
- `RDS_USERNAME`
- `RDS_PASSWORD`
- `RDS_HOSTNAME`
- `RDS_PORT`

### EB CLI deploy steps

Run from `C:\Users\PR.PRADEEKSHA\Desktop\HCL_TRMS\trms_project`

1. `eb init -p python-3.11 trms-project`
2. `eb create trms-production`
3. `eb setenv DJANGO_SECRET_KEY=<strong-secret> DJANGO_DEBUG=false DJANGO_ALLOWED_HOSTS=<your-eb-domain> DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-eb-domain>`
4. `eb deploy`
5. `eb open`

### Important production note

Your current media uploads use the local filesystem. That works for development, but for real AWS production you should move media storage to Amazon S3 so uploads survive instance replacement and scaling.
