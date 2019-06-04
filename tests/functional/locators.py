from selenium.webdriver.common.by import By


class LoginPageLocators:
    USER_NAME_INPUT = (By.NAME, "email")
    PASSWORD_INPUT = (By.NAME, "password")
    H1 = (By.TAG_NAME, "H1")
    LOGIN_BUTTON = (By.NAME, "login")


class NavigationLocators:
    LOG_OUT_LINK = (By.XPATH, "//button[text()='Sign out']")


class HeaderLocators:
    SEARCH_INPUT = (By.ID, "site-search-text")
    SEARCH_SUBMIT = (By.CSS_SELECTOR, ".eff-search__input--submit")


class FooterLinkLocators:
    CMS_LINK = (By.LINK_TEXT, "CMS")


class PageLinkLocators:
    HOME_BREADCRUMB = (By.LINK_TEXT, "Ethnicity facts and figures")
    NEW_MEASURE = (By.LINK_TEXT, "Add a measure")

    @staticmethod
    def page_link(link_text):
        return By.LINK_TEXT, link_text

    @staticmethod
    def breadcrumb_link(page):
        return By.LINK_TEXT, page.title


class MeasureActionLocators:
    @staticmethod
    def view_link(measure):
        print("measure_action__view-%s" % measure.guid)
        return By.ID, "measure_action__view-%s" % measure.guid

    @staticmethod
    def delete_link(measure):
        return By.ID, "measure_action__delete-%s" % measure.guid

    @staticmethod
    def title_link(measure):
        return By.LINK_TEXT, measure.title


class CreateMeasureLocators:
    TITLE_INPUT = (By.NAME, "title")
    SAVE_BUTTON = (By.NAME, "save")


class EditMeasureLocators:
    @staticmethod
    def lowest_level_of_geography_radio_button(index_value):
        # index_value should be in the range 0 to 8 - (as per `lowest_level_of_geography` table per 2018-11-19)
        return (By.ID, "lowest_level_of_geography_id-%s" % str(index_value))

    @staticmethod
    def frequency_radio_button(index_value, data_source_index=1):
        # index_value should be in the range 0 to 11 - (as per `frequency_of_release` table per 2018-11-19)
        return (By.ID, "data-source-%s-frequency_of_release_id-%s" % (data_source_index, str(index_value)))

    @staticmethod
    def type_of_data_checkbox(index_value, data_source_index=1):
        # index_value should be in the range 0 to 1 - (as per application.cms.models.TypeOfData per 2018-11-19)
        return (By.ID, "data-source-%s-type_of_data-%s" % (data_source_index, str(index_value)))

    @staticmethod
    def type_of_statistic_radio_button(index_value, data_source_index=1):
        # index_value should be in the range 0 to 4 - (as per `type_of_statistic` table per 2018-11-19)
        return (By.ID, "data-source-%s-type_of_statistic_id-%s" % (data_source_index, str(index_value)))

    STATUS_LABEL = (By.ID, "status")
    LOWEST_LEVEL_OF_GEOGRAPHY_RADIO = (By.XPATH, "//*[@type='radio']")
    SAVE_BUTTON = (By.NAME, "save")
    SAVE_AND_REVIEW_BUTTON = (By.NAME, "save-and-review")
    SEND_TO_DEPARTMENT_REVIEW_BUTTON = (By.ID, "send-to-department-review")
    REJECT_BUTTON = (By.ID, "reject-measure")
    SEND_TO_DRAFT_BUTTON = (By.ID, "send-back-to-draft")
    SEND_TO_APPROVED = (By.ID, "send-to-approved")
    UPDATE_MEASURE = (By.LINK_TEXT, "Update")
    DEPARTMENT_REVIEW_LINK = (By.ID, "review-link-url")

    PREVIEW_LINK = (By.NAME, "preview")
    ADD_DIMENSION_LINK = (By.LINK_TEXT, "Add dimension")
    ADD_SOURCE_DATA_LINK = (By.LINK_TEXT, "Add source data")

    PUBLISHED_AT_DATE_PICKER = (By.NAME, "published_at")
    PUBLISHED_LABEL = (By.NAME, "published")
    TITLE_INPUT = (By.NAME, "title")

    DESCRIPTION_TEXTAREA = (By.NAME, "description")

    MEASURE_SUMMARY_TEXTAREA = (By.NAME, "measure_summary")
    SUMMARY_TEXTAREA = (By.NAME, "summary")
    GEOGRAPHIC_COVERAGE_TEXTAREA = (By.NAME, "geographic_coverage")
    LOWEST_LEVEL_OF_GEOGRAPHY_TEXTAREA = (By.NAME, "lowest_level_of_geography")
    TIME_COVERED_TEXTAREA = (By.NAME, "time_covered")
    NEED_TO_KNOW_TEXTAREA = (By.NAME, "need_to_know")
    ETHNICITY_DEFINITION_DETAIL_TEXTAREA = (By.NAME, "ethnicity_definition_detail")
    ETHNICITY_SUMMARY_DETAIL_TEXTAREA = (By.NAME, "ethnicity_definition_summary")
    DATA_SOURCE_1_TITLE_TEXTAREA = (By.NAME, "data-source-1-title")
    DATA_SOURCE_1_SOURCE_URL_INPUT = (By.NAME, "data-source-1-source_url")
    DATA_SOURCE_1_PUBLISHER_ID_INPUT = (By.ID, "data-source-1-publisher_id")
    DATA_SOURCE_1_PUBLICATION_DATE_INPUT = (By.NAME, "data-source-1-publication_date")
    DATA_SOURCE_1_FREQUENCY_INPUT = (By.NAME, "data-source-1-frequency_of_release_id")
    DATA_SOURCE_1_PURPOSE_TEXTAREA = (By.NAME, "data-source-1-purpose")
    DATA_SOURCE_2_TITLE_TEXTAREA = (By.NAME, "data-source-2-title")
    DATA_SOURCE_2_SOURCE_URL_INPUT = (By.NAME, "data-source-2-source_url")
    DATA_SOURCE_2_PUBLISHER_ID_INPUT = (By.ID, "data-source-2-publisher_id")
    DATA_SOURCE_2_PUBLICATION_DATE_INPUT = (By.NAME, "data-source-2-publication_date")
    DATA_SOURCE_2_FREQUENCY_INPUT = (By.NAME, "data-source-2-frequency_of_release_id")
    DATA_SOURCE_2_PURPOSE_TEXTAREA = (By.NAME, "data-source-2-purpose")
    RELATED_PUBLICATIONS_TEXTAREA = (By.NAME, "related_publications")
    METHODOLOGY_TEXTAREA = (By.NAME, "methodology")
    DATA_TYPE_INPUT = (By.NAME, "data_type")
    SUPPRESSION_RULES_TEXTAREA = (By.NAME, "suppression_rules")
    DISCLOSURE_CONTROLS_TEXTAREA = (By.NAME, "disclosure_controls")
    ESTIMATION_TEXTAREA = (By.NAME, "estimation")
    TYPE_OF_STATISTIC_INPUT = (By.NAME, "type_of_statistic")
    QMI_URL_INPUT = (By.NAME, "qmi_url")
    FURTHER_TECHNICAL_INFORMATION_INPUT = (By.NAME, "further_technical_information")

    UPDATE_CORRECTS_DATA_MISTAKE = (By.NAME, "update_corrects_data_mistake")
    UPDATE_CORRECTS_DATA_MISTAKE = (By.NAME, "update_corrects_measure_version")
    EXTERNAL_EDIT_SUMMARY = (By.ID, "external_edit_summary")


class DimensionPageLocators:
    TITLE_INPUT = (By.NAME, "title")
    TIME_PERIOD_INPUT = (By.NAME, "time_period")
    SUMMARY_TEXTAREA = (By.NAME, "summary")
    SUPPRESSION_RULES_TEXTAREA = (By.NAME, "suppression_rules")
    DISCLOSURE_CONTROL_TEXTAREA = (By.NAME, "disclosure_control")
    TYPE_OF_STATISTIC_INPUT = (By.NAME, "type_of_statistic")
    LOCATION_INPUT = (By.NAME, "location")
    SOURCE_INPUT = (By.NAME, "source")
    SAVE_BUTTON = (By.NAME, "save")
    UPDATE_BUTTON = (By.NAME, "update")
    CREATE_CHART = (By.ID, "create_chart")
    CREATE_TABLE = (By.ID, "create_table")


class SourceDataPageLocators:
    FILE_UPLOAD_INPUT = (By.NAME, "upload")
    TITLE_INPUT = (By.NAME, "title")
    DESCRIPTION_TEXTAREA = (By.NAME, "description")
    SAVE_BUTTON = (By.NAME, "save")


class ChartBuilderPageLocators:
    DATA_TEXT_AREA = (By.ID, "data_text_area")
    CHART_TYPE_SELECTOR = (By.ID, "chart_type_selector")
    BAR_CHART_PRIMARY = (By.ID, "primary_column")
    BAR_CHART_SECONDARY = (By.ID, "secondary_column")
    BAR_CHART_ORDER = (By.ID, "order_column")
    OPTIONS_CHART_TITLE = (By.ID, "chart_title")
    OPTIONS_X_AXIS = (By.ID, "x_axis_label")
    OPTIONS_Y_AXIS = (By.ID, "y_axis_label")
    OPTIONS_NUMBER_FORMAT = (By.ID, "number_format")
    CHART_PREVIEW = (By.ID, "preview")
    CHART_SAVE = (By.ID, "save")
    CHART_BACK = (By.ID, "exit")
    CHART_DATA_OK = (By.ID, "confirm-data")
    CHART_DATA_CANCEL = (By.ID, "cancel-edit-data")
    CHART_EDIT_DATA = (By.ID, "edit-data")
    PANEL_BAR_CHART_PRIMARY = (By.ID, "panel_primary_column")
    PANEL_BAR_CHART_SECONDARY = (By.ID, "panel_grouping_column")
    CHART_ETHNICITY_SETTINGS = (By.ID, "ethnicity_settings")
    CUSTOM_CLASSIFICATION_PANEL = (By.ID, "custom_classification__panel")

    CHART_LINE_X_AXIS = (By.ID, "line__x-axis_column")

    CHART_GROUPED_BAR_DATA_STYLE = (By.ID, "grouped-bar__data_style")
    CHART_GROUPED_BAR_COLUMN = (By.ID, "grouped-bar__bar_column")
    CHART_GROUPED_GROUPS_COLUMN = (By.ID, "grouped-bar__groups_column")

    CHART_COMPONENT_DATA_STYLE = (By.ID, "component__data_style")
    CHART_COMPONENT_SECTION_COLUMN = (By.ID, "component__section_column")
    CHART_COMPONENT_BAR_COLUMN = (By.ID, "component__bar_column")

    CHART_PANEL_DATA_STYLE = (By.ID, "panel-bar__data_style")
    CHART_PANEL_BAR_COLUMN = (By.ID, "panel-bar__bar_column")
    CHART_PANEL_PANEL_COLUMN = (By.ID, "panel-bar__panel_column")

    CHART_PANEL_X_AXIS_COLUMN = (By.ID, "panel-line__x-axis_column")


class TableBuilderPageLocators:
    DATA_TEXT_AREA = (By.ID, "data_text_area")
    TABLE_TITLE_BOX = (By.ID, "table_title")
    ROWS_SELECTOR = (By.ID, "table_category_column")
    GROUPING_SELECTOR = (By.ID, "table_group_column")
    TABLE_PREVIEW = (By.ID, "preview")
    TABLE_SAVE = (By.ID, "save")
    TABLE = (By.ID, "container")
    TABLE_ERROR_CONTAINER = (By.ID, "error_container")

    COLUMN_SELECTOR_1 = (By.ID, "table_column_1")
    COLUMN_SELECTOR_2 = (By.ID, "table_column_2")
    COLUMN_SELECTOR_3 = (By.ID, "table_column_3")
    COLUMN_SELECTOR_4 = (By.ID, "table_column_4")
    COLUMN_SELECTOR_5 = (By.ID, "table_column_5")

    INDEX_COLUMN_NAME = (By.ID, "index_column_name")

    TABLE_DATA_OK = (By.ID, "confirm-data")
    TABLE_DATA_CANCEL = (By.ID, "cancel-edit-data")
    TABLE_DATA_EDIT = (By.ID, "edit-data")

    TABLE_ETHNICITY_SETTINGS = (By.ID, "ethnicity_settings")
    CUSTOM_CLASSIFICATION_PANEL = (By.ID, "custom_classification__panel")
    COMPLEX_TABLE_DATA_STYLE = (By.ID, "complex-table__data-style")
    COMPLEX_TABLE_COLUMNS = (By.ID, "ethnicity-as-row__columns")
    COMPLEX_TABLE_ROWS = (By.ID, "ethnicity-as-column__rows")


class TopicPageLocators:
    @staticmethod
    def get_accordion(data_event_text):
        return By.XPATH, "//h2[contains(., '%s')]" % data_event_text

    @staticmethod
    def get_add_measure_link(link_text):
        return By.LINK_TEXT, "Create a new page"

    @staticmethod
    def get_measure_link(measure):
        return By.LINK_TEXT, measure.title

    @staticmethod
    def get_measure_edit_link(measure):
        return By.ID, "measure-action-section__edit_button-%s" % measure.id

    @staticmethod
    def get_measure_view_form_link(measure):
        return By.ID, "measure-action-section__view_form_link-%s" % measure.id

    @staticmethod
    def get_measure_create_new_link(measure):
        return By.ID, "measure-action-section__create_new_link-%s" % measure.id

    @staticmethod
    def get_measure_delete_link(measure):
        return By.ID, "measure-action-section__delete_button-%s" % measure.id

    @staticmethod
    def get_measure_confirm_yes_radio(measure):
        return By.ID, "delete-radio-yes-%s" % measure.id

    @staticmethod
    def get_measure_confirm_no_radio(measure):
        return By.ID, "delete-radio-yes-%s" % measure.id

    @staticmethod
    def get_measure_confirm_delete_button(measure):
        return By.ID, "delete-confirm-button-%s" % measure.id
