import logging

from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.exceptions import ClassificationNotFoundException

from application.cms.models import Page, Dimension, Classification, ClassificationValue, DimensionClassification

from application.utils import setup_module_logging, get_bool

logger = logging.Logger(__name__)

"""
The classification service is in charge of management for classifications and values

Classifications
ClassificationValues

which chain together in many-to-many relationships

"""


class ClassificationService:
    def __init__(self):
        self.logger = logger

    def init_app(self, app):
        self.logger = setup_module_logging(self.logger, app.config["LOG_LEVEL"])
        self.logger.info("Initialised classification service")

    """
    CLASSIFICATION Management
    """

    def create_classification(self, code, family, subfamily, title, position=999, long_title=None):
        classification_long_title = title if long_title is None else long_title

        try:
            classification = self.get_classification_by_code(family, code)
        except ClassificationNotFoundException as e:
            classification = Classification(
                code=code,
                title=title,
                family=family,
                subfamily=subfamily,
                long_title=classification_long_title,
                position=position,
            )
            db.session.add(classification)
            db.session.commit()
        return classification

    def create_classification_with_values(
        self, code, family, subfamily, title, long_title=None, position=999, values=[], values_as_parent=[]
    ):
        classification = self.create_classification(code, family, subfamily, title, position, long_title)
        self.add_values_to_classification(classification, values)
        self.add_values_to_classification_as_parents(classification, values_as_parent)

        return classification

    def update_classification(self, classification):
        db.session.add(classification)
        db.session.commit()

    def delete_classification(self, classification):
        self.delete_unused_values_from_database(classification)
        db.session.delete(classification)
        db.session.commit()

    def delete_unused_values_from_database(self, classification):
        if DimensionClassification.query.filter_by(classification_id=classification.id).count() == 0:
            self.remove_classification_values(classification)

    @staticmethod
    def get_classification_by_code(family, code):
        try:
            return Classification.query.filter_by(code=code, family=family).one()
        except NoResultFound as e:
            raise ClassificationNotFoundException("Classification %s not found in family %s" % (code, family))

    @staticmethod
    def get_classification_by_title(family, title):
        try:
            return Classification.query.filter_by(title=title, family=family).one()
        except NoResultFound as e:
            raise ClassificationNotFoundException("Classification %s not found in family %s" % (title, family))

    @staticmethod
    def get_classification_by_id(classification_id):
        try:
            return Classification.query.get(classification_id)
        except NoResultFound as e:
            raise ClassificationNotFoundException("Classification with id %s not found" % classification_id)

    @staticmethod
    def get_all_classifications():
        return Classification.query.all()

    @staticmethod
    def get_ethnicity_classifications():
        return ClassificationService.get_classifications_by_family("Ethnicity")

    @staticmethod
    def get_classifications_by_family(family):
        classifications = Classification.query.filter_by(family=family)

        # get a list of unique subfamilies
        subfamilies = list(set([classification.subfamily for classification in classifications]))
        subfamilies.sort()

        # get a list of categories for each subfamily
        results = []
        for subfamily in subfamilies:
            results = results + [
                {
                    "subfamily": subfamily,
                    "classifications": Classification.query.filter_by(family=family, subfamily=subfamily).order_by(
                        Classification.position
                    ),
                }
            ]
        return results

    @staticmethod
    def edit_classification(classification, family_update, subfamily_update, title_update, position_update):
        classification.family = family_update
        classification.subfamily = subfamily_update
        classification.title = title_update
        classification.position = position_update
        db.session.add(classification)
        db.session.commit()

    """
    VALUE management
    """

    @staticmethod
    def get_value(value):
        return ClassificationValue.query.filter_by(value=value).first()

    @staticmethod
    def get_all_values():
        values = ClassificationValue.query.all()
        return [v.value for v in values]

    @staticmethod
    def get_value_by_uri(uri):
        from slugify import slugify

        value_list = [v for v in ClassificationValue.query.all() if slugify(v.value) == uri]
        return value_list[0] if len(value_list) > 0 else None

    @staticmethod
    def get_all_classification_values():
        return ClassificationValue.query.all()

    def create_value(self, value_string, position=999):
        classification_value = self.get_value(value=value_string)
        if classification_value:
            return classification_value
        else:
            classification_value = ClassificationValue(value=value_string, position=position)
            db.session.add(classification_value)
            db.session.commit()
            return classification_value

    def create_or_get_value(self, value_string, position=999):
        classification_value = self.get_value(value=value_string)
        if classification_value:
            return classification_value
        else:
            return self.create_value(value_string=value_string, position=position)

    def update_value_position(self, value_string, value_position):
        classification_value = self.get_value(value=value_string)
        if classification_value:
            classification_value.position = value_position
            db.session.add(classification_value)
            db.session.commit()
            return classification_value
        return None

    @staticmethod
    def clean_value_database():
        values = ClassificationValue.query.all()
        for value in values:
            if len(value.classifications) == 0:
                db.session.delete(value)
                db.session.commit()

    """
    CATEGORY >-< VALUE relationship management
    """

    def add_value_to_classification(self, classification, value_title):
        value = self.create_or_get_value(value_string=value_title)
        classification.values.append(value)

        db.session.add(classification)
        db.session.commit()
        return classification

    def add_value_to_classification_as_parent(self, classification, value_string):
        value = self.create_or_get_value(value_string=value_string)
        classification.parent_values.append(value)

        db.session.add(classification)
        db.session.commit()
        return classification

    def add_values_to_classification(self, classification, value_strings):
        for value_string in value_strings:
            value = self.create_or_get_value(value_string=value_string)
            classification.values.append(value)
        db.session.add(classification)
        db.session.commit()
        return classification

    def add_values_to_classification_as_parents(self, classification, value_strings):
        for value_string in value_strings:
            value = self.create_or_get_value(value_string=value_string)
            classification.parent_values.append(value)
        db.session.add(classification)
        db.session.commit()
        return classification

    def remove_value_from_classification(self, classification, value_string):
        value = self.get_value(value=value_string)

        classification.values.remove(value)
        db.session.add(classification)
        db.session.commit()

    def remove_parent_value_from_classification(self, classification, value_string):
        value = self.get_value(value=value_string)

        classification.parent_values.remove(value)
        db.session.add(classification)
        db.session.commit()

    @staticmethod
    def remove_classification_values(classification):
        for value in classification.values:
            db.session.delete(value)
        db.session.commit()

    @staticmethod
    def remove_parent_classification_values(classification):
        for value in classification.parent_values:
            db.session.delete(value)
        db.session.commit()


classification_service = ClassificationService()
