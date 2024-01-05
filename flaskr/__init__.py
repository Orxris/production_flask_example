"""
Production Flask Example

"""

from flask import Flask, request
from celery import Celery, Task, shared_task


def create_celery_app(app):
    """
    Create Celery App

    Creates a celery app object using config details from the Flask app
    sent as the first positional argument.
    """

    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    return celery_app


def create_app(test_config=None):
    """
    Create App

    Creates a flask app, and calls the create_celery_app function too.
    """

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        CELERY={
            "broker_url": "redis://localhost",
            "result_backend": "redis://localhost",
            "task_ignore_result": True,
        }
    )

    # This is a route that does not depend on celery
    # If this works, then the flask app is 'working'.
    @app.route("/hello")
    def hello():
        return "hello world"

    app.extensions["celery"] = create_celery_app(app)

    # This is the celery task itself
    @shared_task(ignore_result=False)
    def add_together(a, b):
        return a + b

    # Here we have the route with the celery task.
    # At the moment it just returns the id of the result, not the
    # actual value.
    @app.route("/add")
    def add():
        a = request.args.get("a")
        b = request.args.get("b")
        result = add_together.delay(float(a), float(b))
        return "result:" + str(result)

    return app
