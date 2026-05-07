import os
import click
from flask.cli import with_appcontext

from app import db
from app.models import User, Source, UserRole


@click.command('seed-users')
@with_appcontext
def seed_users_command():
    """Seeds the database with default Admin, Analyst, and User accounts from ENV secrets."""
    roles = [UserRole.ADMIN, UserRole.ANALYST, UserRole.USER]
    created = 0

    for role in roles:
        email = os.environ.get(f'SEED_{role.upper()}_EMAIL')
        password = os.environ.get(f'SEED_{role.upper()}_PASSWORD')

        if not email or not password:
            print(f"Skipping {role} creation: Missing SEED_{role.upper()}_EMAIL or SEED_{role.upper()}_PASSWORD in .env")
            continue

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"{role} user already exists with email: {email}")
            continue

        new_user = User(email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        created += 1
        print(f"Created {role} user: {email}")

    if created > 0:
        db.session.commit()
        print(f"Successfully seeded {created} new users.")
    else:
        print("No new users were created.")


@click.command('seed-sources')
@with_appcontext
def seed_sources_command():
    """Seeds the database with default scraping sources."""
    meget = Source.query.filter_by(name='MEGET').first()
    if not meget:
        meget = Source(name='MEGET', base_url='https://meget.kiev.ua/prodazha-kvartir/')
        db.session.add(meget)

    bon_ua = Source.query.filter_by(name='BON.UA').first()
    if not bon_ua:
        bon_ua = Source(name='BON.UA', base_url='https://bon.ua/nedvizhimost/prodazha-kvartir')
        db.session.add(bon_ua)

    db.session.commit()
    print("Sources seeded successfully.")
