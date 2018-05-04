import time

from faker import Faker
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import _find_element
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from tests.functional.elements import UsernameInputElement, PasswordInputElement
from tests.functional.locators import (
    NavigationLocators,
    LoginPageLocators,
    FooterLinkLocators,
    PageLinkLocators,
    CreateMeasureLocators,
    EditMeasureLocators,
    DimensionPageLocators,
    MeasureActionLocators,
    ChartBuilderPageLocators,
    TableBuilderPageLocators,
    TopicPageLocators
)


class RetryException(Exception):
    pass


class BasePage:
    log_out_link = NavigationLocators.LOG_OUT_LINK

    def __init__(self, driver, base_url):
        self.driver = driver
        # We've been getting intermittent "Connection reset by peer" errors during test runs in our CI environment
        # Increasing the page_load_timeout here will hopefully prevent (or at least reduce) these errors
        self.driver.set_page_load_timeout(60)
        self.base_url = base_url

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def wait_for_seconds(self, seconds):
        time.sleep(seconds)

    def wait_for_invisible_element(self, locator):
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_element(self, locator):
        element = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(locator),
            EC.presence_of_element_located(locator)
        )
        return element

    def wait_until_select_contains(self, locator, text):
        return WebDriverWait(self.driver, 10, 1).until(
            select_contains(locator, text)
        )

    def scroll_and_click(self, element):
        body = self.driver.find_element_by_css_selector('body')

        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.send_keys_to_element(body, 8 * Keys.ARROW_UP)
        actions.move_to_element(element)
        actions.click(element)
        actions.perform()

    def scroll_to(self, element):
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()

    def log_out(self):
        element = self.wait_for_element(BasePage.log_out_link)
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.click(element)
        actions.perform()
        self.driver.delete_all_cookies()

    def wait_until_url_is(self, url):
        element = WebDriverWait(self.driver, 10).until(
            self.url_contains(url)
        )
        return element

    def wait_until_url_contains(self, text):
        element = WebDriverWait(self.driver, 10).until(
            self.url_contains(text)
        )
        print(text in self.driver.current_url)
        return element

    def wait_until_url_does_not_contain(self, text):
        element = WebDriverWait(self.driver, 10).until(
            self.url_does_not_contain(text)
        )
        print(text in self.driver.current_url)
        return element

    def url_contains(self, url):
        def check_contains_url(driver):
            return url in driver.current_url

        return check_contains_url

    def url_does_not_contain(self, url):
        def check_does_not_contain(driver):
            return url not in driver.current_url

        return check_does_not_contain

    def select_checkbox_or_radio(self, element):
        self.driver.execute_script("arguments[0].setAttribute('checked', 'checked')", element)


class select_contains(object):
    def __init__(self, locator, text):
        self.locator = locator
        self.text = text

    def __call__(self, driver):
        options = _find_element(driver, self.locator).find_elements_by_tag_name('option')
        for option in options:
            if option.text == self.text:
                return True
        return False


class LogInPage(BasePage):
    login_button = LoginPageLocators.LOGIN_BUTTON
    username_input = UsernameInputElement()
    password_input = PasswordInputElement()

    def __init__(self, driver, live_server):
        super().__init__(driver=driver, base_url='http://localhost:%s' % live_server.port)

    def get(self):
        url = '%s/auth/login' % self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is('%s/auth/login' % self.base_url)

    def fill_login_form(self, username, password):
        self.username_input = username
        self.password_input = password

    def click_login_button(self):
        element = self.wait_for_element(LogInPage.login_button)
        element.click()

    def login(self, username, password):
        self.fill_login_form(username, password)
        self.click_login_button()


class HomePage(BasePage):
    cms_link = FooterLinkLocators.CMS_LINK

    def __init__(self, driver, live_server):
        super().__init__(driver=driver, base_url='http://localhost:%s' % live_server.port)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def click_cms_link(self):
        element = self.wait_for_element(HomePage.cms_link)
        element.click()

    def click_topic_link(self, topic):
        element = self.wait_for_element(PageLinkLocators.page_link(topic.title))
        element.click()


class CmsIndexPage(BasePage):

    def __init__(self, driver, live_server):
        super().__init__(driver=driver, base_url='http://localhost:%s/cms' % live_server.port)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def click_topic_link(self, page):
        element = self.wait_for_element(PageLinkLocators.page_link(page.title))
        self.scroll_and_click(element)


class TopicPage(BasePage):

    def __init__(self, driver, live_server, page):
        super().__init__(driver=driver, base_url='http://localhost:%s/%s' % (live_server.port,
                                                                             page.guid.replace('topic_', '')))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def expand_accordion_for_subtopic(self, subtopic):
        element = self.wait_for_element(TopicPageLocators.get_accordion(subtopic.title))
        self.scroll_and_click(element)

    def click_breadcrumb_for_home(self):
        element = self.wait_for_element(PageLinkLocators.HOME_BREADCRUMB)
        self.scroll_and_click(element)

    def click_add_measure(self, subtopic):
        element = self.wait_for_element(TopicPageLocators.get_add_measure_link(subtopic.title))
        self.scroll_and_click(element)

    def click_get_measure(self, measure):
        element = self.wait_for_element(PageLinkLocators.page_link(measure.title))
        self.scroll_and_click(element)

    def click_preview_measure(self, measure):
        element = self.wait_for_element(MeasureActionLocators.view_link(measure))
        self.scroll_and_click(element)

    def measure_is_listed(self, measure):
        try:
            locator = TopicPageLocators.get_measure_link(measure)
            self.driver.find_element(locator[0], locator[1])
        except NoSuchElementException:
            return False
        return True

    def click_edit_button(self, measure):
        element = self.wait_for_element(TopicPageLocators.get_measure_edit_link(measure))
        self.scroll_and_click(element)

    def click_view_form_button(self, measure):
        element = self.wait_for_element(TopicPageLocators.get_measure_view_form_link(measure))
        self.scroll_and_click(element)

    def click_create_new_button(self, measure):
        element = self.wait_for_element(TopicPageLocators.get_measure_create_new_link(measure))
        self.scroll_and_click(element)

    def click_delete_button(self, measure):
        element = self.wait_for_element(TopicPageLocators.get_measure_delete_link(measure))
        self.scroll_and_click(element)

    def select_yes_radio(self, measure):
        locator = TopicPageLocators.get_measure_confirm_yes_radio(measure)
        element = self.driver.find_element(locator[0], locator[1])
        self.scroll_and_click(element)

    def click_confirm_delete(self, measure):
        locator = TopicPageLocators.get_measure_confirm_delete_button(measure)
        element = self.driver.find_element(locator[0], locator[1])
        self.scroll_and_click(element)


class SubtopicPage(BasePage):

    def __init__(self, driver, live_server, topic_page, subtopic_page):
        super().__init__(driver=driver, base_url='http://localhost:%s/cms/%s/%s'
                                                 % (live_server.port, topic_page.guid, subtopic_page.guid))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def click_measure_link(self, page):
        element = self.wait_for_element(PageLinkLocators.page_link(page.title))
        self.scroll_and_click(element)

    def click_preview_measure_link(self, page):
        element = self.wait_for_element(PageLinkLocators.page_link(page.title))
        self.scroll_and_click(element)

    def click_breadcrumb_for_page(self, page):
        element = self.wait_for_element(PageLinkLocators.breadcrumb_link(page))
        self.scroll_and_click(element)

    def click_breadcrumb_for_home(self):
        element = self.wait_for_element(PageLinkLocators.HOME_BREADCRUMB)
        self.scroll_and_click(element)

    def click_new_measure(self):
        element = self.wait_for_element(PageLinkLocators.NEW_MEASURE)
        self.scroll_and_click(element)


class MeasureCreatePage(BasePage):

    def __init__(self, driver, live_server, topic, subtopic):
        super().__init__(driver=driver, base_url='http://localhost:%s/cms/%s/%s/measure/new'
                                                 % (live_server.port, topic.guid, subtopic.guid))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def set_title(self, title):
        element = self.wait_for_element(CreateMeasureLocators.TITLE_INPUT)
        element.clear()
        element.send_keys(title)

    def click_save(self):
        element = self.wait_for_element(CreateMeasureLocators.SAVE_BUTTON)
        self.scroll_and_click(element)


class MeasureVersionsPage(BasePage):

    def __init__(self, driver, live_server, topic_page, subtopic_page, measure_page_guid):
        super().__init__(driver=driver,
                         base_url='http://localhost:%s/cms/%s/%s/%s/versions'
                                  % (live_server.port,
                                     topic_page.guid,
                                     subtopic_page.guid,
                                     measure_page_guid,))

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def click_measure_version_link(self, page):
        link_text = 'Version %s - %s' % (page.version, page.created_at.strftime('%d %B %Y'))
        element = self.wait_for_element(PageLinkLocators.page_link(link_text))
        element.click()


class MeasureEditPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver=driver,
                         base_url=driver.current_url)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def get_status(self):
        element = self.wait_for_element(EditMeasureLocators.STATUS_LABEL)
        return element.text

    def get_review_link(self):
        locator = EditMeasureLocators.DEPARTMENT_REVIEW_LINK
        element = self.driver.find_element(locator[0], locator[1])
        return element.get_attribute('href')

    def click_breadcrumb_for_page(self, page):
        element = self.wait_for_element(PageLinkLocators.breadcrumb_link(page))
        self.scroll_and_click(element)

    def click_breadcrumb_for_home(self):
        element = self.wait_for_element(PageLinkLocators.HOME_BREADCRUMB)
        self.scroll_and_click(element)

    def click_save(self):
        element = self.wait_for_element(EditMeasureLocators.SAVE_BUTTON)
        self.scroll_and_click(element)

    def click_save_and_send_to_review(self):
        element = self.wait_for_element(EditMeasureLocators.SAVE_AND_REVIEW_BUTTON)
        self.scroll_and_click(element)

    def click_add_dimension(self):
        element = self.wait_for_invisible_element(EditMeasureLocators.ADD_DIMENSION_LINK)
        self.scroll_to(element)
        element.click()

    def click_preview(self):
        element = self.wait_for_element(EditMeasureLocators.PREVIEW_LINK)
        self.scroll_and_click(element)

    def click_department_review(self):
        element = self.wait_for_element(EditMeasureLocators.SEND_TO_DEPARTMENT_REVIEW_BUTTON)
        self.scroll_and_click(element)

    def approved_is_visible(self):
        try:
            locator = EditMeasureLocators.SEND_TO_APPROVED
            self.driver.find_element(locator[0], locator[1])
        except NoSuchElementException:
            return False
        return True

    def click_approved(self):
        element = self.wait_for_element(EditMeasureLocators.SEND_TO_APPROVED)
        self.scroll_and_click(element)

    def set_text_field(self, locator, value):
        element = self.wait_for_element(locator)
        element.clear()
        element.send_keys(value)

    def set_auto_complete_field(self, locator, value):
        body = self.driver.find_element_by_tag_name('body')
        element = self.wait_for_element(locator)

        body.send_keys(Keys.CONTROL + Keys.HOME)
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.send_keys_to_element(body, 8 * Keys.ARROW_UP)
        actions.move_to_element(element)
        actions.perform()

        element.clear()
        element.send_keys(value)

    def set_title(self, title):
        self.set_text_field(EditMeasureLocators.TITLE_INPUT, title)

    def set_publication_date(self, date):
        element = self.wait_for_element(EditMeasureLocators.PUBLICATION_DATE_PICKER)
        # element.clear()
        element.send_keys(date)

    def set_measure_summary(self, measure_summary):
        self.set_text_field(EditMeasureLocators.MEASURE_SUMMARY_TEXTAREA, measure_summary)

    def set_main_points(self, main_points):
        self.set_text_field(EditMeasureLocators.MAIN_POINTS_TEXTAREA, main_points)

    def set_time_period_covered(self, value):
        self.set_text_field(EditMeasureLocators.TIME_COVERED_TEXTAREA, value)

    def set_area_covered(self, area_id):
        element = self.driver.find_element('id', area_id)
        self.select_checkbox_or_radio(element)

    def set_lowest_level_of_geography(self, lowest_level):
        locator = EditMeasureLocators.lowest_level_of_geography_radio_button(0)
        element = self.driver.find_element(locator[0], locator[1])
        self.select_checkbox_or_radio(element)

    def set_primary_title(self, value):
        self.set_text_field(EditMeasureLocators.SOURCE_TEXT_TEXTAREA, value)

    def set_primary_publisher(self, value):
        self.set_auto_complete_field(EditMeasureLocators.DEPARTMENT_SOURCE_TEXTAREA, value)

    def set_primary_url(self, value):
        self.set_text_field(EditMeasureLocators.SOURCE_URL_INPUT, value)

    def set_last_update(self, value):
        self.set_text_field(EditMeasureLocators.LAST_UPDATE_INPUT, value)

    def set_things_you_need_to_know(self, value):
        self.set_text_field(EditMeasureLocators.NEED_TO_KNOW_TEXTAREA, value)

    def set_what_the_data_measures(self, value):
        self.set_text_field(EditMeasureLocators.MEASURE_SUMMARY_TEXTAREA, value)

    def set_ethnicity_categories(self, value):
        self.set_text_field(EditMeasureLocators.ETHNICITY_SUMMARY_DETAIL_TEXTAREA, value)

    def set_primary_frequency(self):
        locator = EditMeasureLocators.frequency_radio_button(0)
        element = self.driver.find_element(locator[0], locator[1])
        self.scroll_and_click(element)

    def set_primary_type_of_statistic(self):
        locator = EditMeasureLocators.type_of_statistic_radio_button(0)
        element = self.driver.find_element(locator[0], locator[1])
        self.select_checkbox_or_radio(element)

    def set_primary_source_type_of_data(self, data_id):
        element = self.driver.find_element('id', data_id)
        self.select_checkbox_or_radio(element)

    def set_purpose(self, value):
        self.set_text_field(EditMeasureLocators.DATA_SOURCE_PURPOSE_TEXTAREA, value)

    def set_methodology(self, value):
        self.set_text_field(EditMeasureLocators.METHODOLOGY_TEXTAREA, value)

    def fill_measure_page(self, page):
        self.set_time_period_covered(page.time_covered)
        self.set_area_covered(area_id='england')
        self.set_lowest_level_of_geography(lowest_level='0')

        self.set_primary_title(value=page.source_text)
        self.set_primary_publisher(value='DWP\n')
        self.set_primary_url(value=page.source_url)
        self.set_primary_frequency()
        self.set_primary_type_of_statistic()

        self.set_measure_summary(page.measure_summary)
        self.set_main_points(page.main_points)
        self.set_things_you_need_to_know(page.need_to_know)
        self.set_what_the_data_measures(page.measure_summary)
        self.set_ethnicity_categories(page.ethnicity_definition_summary)
        self.set_primary_source_type_of_data('administrative_data')
        self.set_purpose(page.data_source_purpose)
        self.set_methodology(page.methodology)


class DimensionAddPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver=driver,
                         base_url=driver.current_url)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.wait_until_url_is(self.base_url)

    def set_title(self, title):
        element = self.wait_for_element(DimensionPageLocators.TITLE_INPUT)
        element.clear()
        element.send_keys(title)

    def set_time_period(self, time_period):
        element = self.wait_for_element(DimensionPageLocators.TIME_PERIOD_INPUT)
        element.clear()
        element.send_keys(time_period)

    def set_summary(self, summary):
        element = self.wait_for_element(DimensionPageLocators.SUMMARY_TEXTAREA)
        element.clear()
        element.send_keys(summary)

    def set_category(self, category):
        element = self.wait_for_element(DimensionPageLocators.SUMMARY_TEXTAREA)
        element.clear()
        element.send_keys(category)

    def click_save(self):
        element = self.wait_for_element(DimensionPageLocators.SAVE_BUTTON)
        self.scroll_and_click(element)


class DimensionEditPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver=driver,
                         base_url=driver.current_url)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.source_contains('Edit dimension')

    def source_contains(self, text):
        return text in self.driver.page_source

    def click_update(self):
        element = self.wait_for_element(DimensionPageLocators.UPDATE_BUTTON)
        element.click()

    def click_create_chart(self):
        element = self.wait_for_element(DimensionPageLocators.CREATE_CHART)
        element.click()

    def click_create_table(self):
        element = self.wait_for_element(DimensionPageLocators.CREATE_TABLE)
        element.click()

    def set_summary(self, summary):
        element = self.wait_for_element(DimensionPageLocators.SUMMARY_TEXTAREA)
        element.clear()
        element.send_keys(summary)


class MeasurePreviewPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver=driver,
                         base_url=driver.current_url)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def source_contains(self, text):
        return text in self.driver.page_source


class ChartBuilderPage(BasePage):

    def __init__(self, driver, dimension_page):
        super().__init__(driver=driver,
                         base_url=driver.current_url)
        self.dimension_url = dimension_page.base_url

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.url_contains(self.dimension_url[0:-5]) \
               and self.url_contains('create_chart') \
               and self.source_contains('Add Chart')

    def paste_data(self, data):
        lines = ['|'.join(line) for line in data]
        text_block = '\n'.join(lines)

        element = self.wait_for_element(ChartBuilderPageLocators.DATA_TEXT_AREA)
        self.scroll_to(element)
        element.clear()
        element.send_keys(text_block)

    def select_chart_type(self, chart_type):
        # self.wait_until_select_contains(ChartBuilderPageLocators.CHART_TYPE_SELECTOR, chart_type)

        element = self.wait_for_element(ChartBuilderPageLocators.CHART_TYPE_SELECTOR)
        self.scroll_to(element)
        select = Select(element)
        select.select_by_visible_text(chart_type)
        self.wait_until_select_contains(ChartBuilderPageLocators.CHART_TYPE_SELECTOR, 'Bar chart')

    def select_bar_chart_category(self, category_column):
        if select_contains(ChartBuilderPageLocators.BAR_CHART_PRIMARY, category_column):
            element = self.wait_for_element(ChartBuilderPageLocators.BAR_CHART_PRIMARY)
            self.scroll_to(element)

            select = Select(element)
            if select.first_selected_option.text != category_column:
                select.select_by_visible_text(category_column)
                self.wait_until_select_contains(ChartBuilderPageLocators.BAR_CHART_PRIMARY, category_column)

    def select_bar_chart_group(self, group_column):
        if select_contains(ChartBuilderPageLocators.BAR_CHART_SECONDARY, group_column):
            element = self.wait_for_element(ChartBuilderPageLocators.BAR_CHART_SECONDARY)
            self.scroll_to(element)

            select = Select(element)
            if select.first_selected_option.text != group_column:
                select.select_by_visible_text(group_column)
                self.wait_until_select_contains(ChartBuilderPageLocators.BAR_CHART_SECONDARY, group_column)

    def select_panel_bar_chart_primary(self, category_column):
        if select_contains(ChartBuilderPageLocators.PANEL_BAR_CHART_PRIMARY, category_column):
            element = self.wait_for_element(ChartBuilderPageLocators.PANEL_BAR_CHART_PRIMARY)
            self.scroll_to(element)

            select = Select(element)
            select.select_by_visible_text(category_column)
            self.wait_until_select_contains(ChartBuilderPageLocators.PANEL_BAR_CHART_PRIMARY, category_column)

    def select_panel_bar_chart_grouping(self, group_column):
        if select_contains(ChartBuilderPageLocators.PANEL_BAR_CHART_SECONDARY, group_column):
            element = self.wait_for_element(ChartBuilderPageLocators.PANEL_BAR_CHART_SECONDARY)
            self.scroll_to(element)

            select = Select(element)
            select.select_by_visible_text(group_column)
            self.wait_until_select_contains(ChartBuilderPageLocators.PANEL_BAR_CHART_SECONDARY, group_column)

    def click_preview(self):
        element = self.wait_for_element(ChartBuilderPageLocators.CHART_PREVIEW)
        self.scroll_to(element)
        element.click()

    def click_save(self):
        element = self.wait_for_element(ChartBuilderPageLocators.CHART_SAVE)
        self.scroll_to(element)
        element.click()

    def click_back(self):
        element = self.wait_for_element(ChartBuilderPageLocators.CHART_BACK)
        self.scroll_to(element)
        element.click()

    def source_contains(self, text):
        return text in self.driver.page_source

    def url_contains(self, url):
        return url in self.driver.current_url


class TableBuilderPage(BasePage):

    def __init__(self, driver):
        super().__init__(driver=driver,
                         base_url=driver.current_url)

    def get(self):
        url = self.base_url
        self.driver.get(url)

    def is_current(self):
        return self.source_contains('Add Table')

    def paste_data(self, data):
        lines = ['|'.join(line) for line in data]
        text_block = '\n'.join(lines)

        element = self.wait_for_element(TableBuilderPageLocators.DATA_TEXT_AREA)
        self.scroll_to(element)
        element.clear()
        element.send_keys(text_block)

    def select_category(self, category):
        self.wait_until_select_contains(TableBuilderPageLocators.ROWS_SELECTOR, category)

        element = self.wait_for_element(TableBuilderPageLocators.ROWS_SELECTOR)
        select = Select(element)
        select.select_by_visible_text(category)

    def select_grouping(self, grouping):
        self.wait_until_select_contains(TableBuilderPageLocators.GROUPING_SELECTOR, grouping)

        element = self.wait_for_element(TableBuilderPageLocators.GROUPING_SELECTOR)
        select = Select(element)
        select.select_by_visible_text(grouping)

    def select_column_1(self, column_1):
        self.wait_until_select_contains(TableBuilderPageLocators.COLUMN_SELECTOR_1, column_1)

        element = self.wait_for_element(TableBuilderPageLocators.COLUMN_SELECTOR_1)
        select = Select(element)
        select.select_by_visible_text(column_1)

    def click_preview(self):
        element = self.wait_for_element(TableBuilderPageLocators.TABLE_PREVIEW)
        self.scroll_to(element)
        element.click()

    def click_save(self):
        element = self.wait_for_element(TableBuilderPageLocators.TABLE_SAVE)
        self.scroll_to(element)
        element.click()

    def source_contains(self, text):
        return text in self.driver.page_source


class RandomMeasure:

    def __init__(self):
        factory = Faker()
        self.guid = '%s_%s' % (factory.word(), factory.random_int(1, 1000))
        self.version = '1.0'
        self.publication_date = factory.date('%d%m%Y')
        self.published = False
        self.title = ' '.join(factory.words(4))
        self.measure_summary = factory.text()
        self.main_points = factory.text()
        self.lowest_level_of_geography = factory.text(100)
        self.time_covered = factory.text(100)
        self.need_to_know = factory.text()
        self.ethnicity_definition_detail = factory.text()
        self.ethnicity_definition_summary = factory.text()
        self.source_text = factory.text(100)
        self.source_url = factory.url()
        self.department_source = factory.text(100)
        self.published_date = factory.date()
        self.last_update = factory.date()
        self.next_update = factory.date()
        self.frequency = factory.word()
        self.related_publications = factory.text()
        self.contact_phone = factory.phone_number()
        self.contact_email = factory.company_email()
        self.data_source_purpose = factory.text()
        self.methodology = factory.text()
        self.data_type = factory.word()
        self.suppression_rules = factory.text()
        self.disclosure_controls = factory.text()
        self.estimation = factory.word()
        self.type_of_statistic = factory.word()
        self.qui_url = factory.url()
        self.further_technical_information = factory.text()


class RandomDimension():
    def __init__(self):
        factory = Faker()
        self.title = ' '.join(factory.words(4))
        self.time_period = ' '.join(factory.words(4))
        self.summary = factory.text(100)
        self.suppression_rules = factory.text(100)
        self.disclosure_control = factory.text(100)
        self.type_of_statistic = ' '.join(factory.words(4))
        self.location = ' '.join(factory.words(4))
        self.source = ' '.join(factory.words(4))
