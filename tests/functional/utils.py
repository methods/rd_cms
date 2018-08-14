from application.cms.page_service import PageService
from tests.functional.pages import HomePage, LogInPage, MeasureCreatePage, MeasureEditPage, RandomMeasure, TopicPage

EXPECTED_STATUSES = {
    "draft": "Status:  Draft",
    "internal_review": "Status:  Internal review",
    "department_review": "Status:  Department review",
    "published": "Status:  Published",
    "rejected": "Status:  Rejected",
}


def assert_page_correct(driver, live_server, stub_topic_page, stub_subtopic_page, page, status):
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)

    assert_page_status(driver, topic_page, page, status)

    topic_page.click_preview_measure(page)
    assert_page_details(driver, page)

    driver.back()


def assert_page_status(driver, topic_page, page, status):
    pass


def assert_page_details(driver, page):
    pass


def create_measure_starting_at_topic_page(driver, live_server, stub_subtopic_page, stub_topic_page):
    """
    CREATE v1 1: Click through to subtopic topic page
    """
    topic_page = TopicPage(driver, live_server, stub_topic_page)
    assert topic_page.is_current()
    topic_page.expand_accordion_for_subtopic(stub_subtopic_page)
    """
    CREATE v1 2: Add measure page
    """
    topic_page.click_add_measure(stub_subtopic_page)
    measure_create_page = MeasureCreatePage(driver, live_server, stub_topic_page, stub_subtopic_page)
    assert measure_create_page.is_current()
    """
    CREATE v1 3: Fill measure create page
    """
    page = RandomMeasure()
    measure_create_page.set_title(page.title)
    measure_create_page.click_save()
    """
    CREATE v1 4: Add some content
    """
    measure_edit_page = MeasureEditPage(driver)
    measure_edit_page.fill_measure_page(page)
    measure_edit_page.click_save()
    """
    CREATE v1 5: Now it has been added we ought to have a generated GUID which we will need so
    we may have to retrieve the page again
    """
    page_service = PageService()
    page = page_service.get_page_with_title(page.title)
    return measure_edit_page, page


def navigate_to_topic_page(driver, live_server, topic_page):
    """
    ENTRY 1: Home page
    """
    home_page = HomePage(driver, live_server)
    home_page.get()
    assert home_page.is_current()
    """
    ENTRY 1: Go to topic page
    """
    home_page.click_topic_link(topic_page)


def navigate_to_preview_page(driver, live_server, topic, subtopic, measure):
    """
    ENTRY 1: Home page
    """
    topic_page = TopicPage(driver, live_server, topic)
    if not topic_page.is_current():
        navigate_to_topic_page(driver, live_server, topic)

    topic_page.expand_accordion_for_subtopic(subtopic)
    topic_page.click_preview_measure(measure)


def navigate_to_edit_page(driver, live_server, topic, subtopic, measure):
    """
    ENTRY 1: Home page
    """
    topic_page = TopicPage(driver, live_server, topic)
    if not topic_page.is_current():
        navigate_to_topic_page(driver, live_server, topic)

    topic_page.expand_accordion_for_subtopic(subtopic)
    topic_page.click_edit_button(measure)


def navigate_to_view_form(driver, live_server, topic, subtopic, measure):
    """
    ENTRY 1: Home page
    """
    topic_page = TopicPage(driver, live_server, topic)
    if not topic_page.is_current():
        navigate_to_topic_page(driver, live_server, topic)

    topic_page.expand_accordion_for_subtopic(subtopic)
    topic_page.click_view_form_button(measure)


def login(driver, live_server, test_app_editor):
    login_page = LogInPage(driver, live_server)
    login_page.get()
    if login_page.is_current():
        login_page.login(test_app_editor.email, test_app_editor.password)
