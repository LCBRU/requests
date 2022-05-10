from lbrc_services.model.services import Organisation, TaskStatusType
from lbrc_flask.database import db


def init_model(app):
    
    @app.before_first_request
    def task_status_type_setup():
        for name, details in TaskStatusType.all_details.items():
            if TaskStatusType.query.filter(TaskStatusType.name == name).count() == 0:
                db.session.add(
                    TaskStatusType(
                        name=name,
                        is_complete=details['is_complete'],
                        is_active=details['is_active'],
                    )
                )

        for name in Organisation.all_organisations:
            if Organisation.query.filter(Organisation.name == name).count() == 0:
                db.session.add(
                    Organisation(
                        name=name,
                    )
                )

        db.session.commit()