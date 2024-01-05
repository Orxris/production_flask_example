import os
from flask import Flask, request
from celery import Celery, Task, shared_task


def create_celery_app(app):
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config['CELERY'])
    celery_app.set_default()
    return celery_app


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        CELERY={
            "broker_url": "redis://localhost",
            "result_backend": "redis://localhost",
            "task_ignore_result": True
        }
    )

    @app.route("/hello")
    def hello():
        return "hello world"

    app.extensions['celery'] = create_celery_app(app)

    @shared_task(ignore_result=False)
    def add_together(a, b):
        return a + b


    @app.route("/add")
    def add():
        a = request.args.get("a")
        b = request.args.get("b")
        result = add_together.delay(float(a), float(b))
        return "result:" + str(result)



    return app

if __name__ == "__main__":
    flask_app = create_app()
    celery_app = flask_app.extensions["celery"]
