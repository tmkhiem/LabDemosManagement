import click
from flask import Flask


def register_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database (create all tables)."""
        from . import db
        with app.app_context():
            db.create_all()
        click.echo("Database initialized.")

    @app.cli.command("create-admin")
    @click.option("--username", required=True, prompt=True, help="Admin username")
    @click.option(
        "--password",
        required=True,
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Admin password",
    )
    @click.option(
        "--display-name", default=None, help="Display name (defaults to username)"
    )
    def create_admin(username, password, display_name):
        """Create an admin user account."""
        from . import db
        from .models import User

        with app.app_context():
            username = username.strip().lower()
            if User.query.filter_by(username=username).first():
                click.echo(f"Error: Username '{username}' already exists.", err=True)
                return
            user = User(
                username=username,
                display_name=display_name or username,
                role="admin",
                is_active=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            click.echo(f"Admin user '{username}' created successfully.")

    @app.cli.command("seed-demo-data")
    def seed_demo_data():
        """Seed sample student and demo data for development."""
        from . import db
        from .models import Demo, User

        with app.app_context():
            # Create sample students
            students = [
                ("alice", "Alice Johnson"),
                ("bob", "Bob Smith"),
                ("carol", "Carol White"),
            ]
            created_students = []
            for uname, dname in students:
                if not User.query.filter_by(username=uname).first():
                    user = User(
                        username=uname,
                        display_name=dname,
                        role="student",
                        is_active=True,
                    )
                    user.set_password("password123")
                    db.session.add(user)
                    db.session.flush()
                    created_students.append(user)
                    click.echo(f"Created student: {uname}")
                else:
                    created_students.append(User.query.filter_by(username=uname).first())

            # Create sample demos
            sample_demos = [
                (created_students[0], "web-app", "http://10.0.0.10:5000", "My Flask web app"),
                (created_students[0], "api-demo", "http://10.0.0.10:8080", "REST API demo"),
                (created_students[1], "ml-dashboard", "http://10.0.0.11:3000", "ML model dashboard"),
                (created_students[2], "chat-app", "http://10.0.0.12:4000", "Real-time chat app"),
            ]
            for owner, dname, url, desc in sample_demos:
                if not Demo.query.filter_by(owner_id=owner.id, demo_name=dname).first():
                    demo = Demo(
                        owner_id=owner.id,
                        demo_name=dname,
                        target_url=url,
                        description=desc,
                    )
                    db.session.add(demo)
                    click.echo(f"Created demo: {owner.username}/{dname}")

            db.session.commit()
            click.echo("Seed data inserted successfully.")
