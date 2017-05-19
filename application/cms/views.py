import json

from flask import (
    redirect,
    render_template,
    request,
    url_for,
    abort,
    flash)

from flask_login import login_required

from application.cms import cms_blueprint

from application.cms.forms import PageForm, MeasurePageForm
from application.cms.exceptions import PageNotFoundException, DimensionNotFoundException
from application.cms.models import publish_status
from application.cms.page_service import page_service


@cms_blueprint.route('/')
@login_required
def index():
    pages = page_service.get_pages()
    return render_template('cms/index.html', pages=pages)


@cms_blueprint.route('/topic/new', methods=['GET', 'POST'])
@login_required
def create_topic_page():
    pages = page_service.get_pages()
    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            page = page_service.create_page(page_type='topic', data=form.data)
            message = 'Created page {}'.format(page.title)
            flash(message, 'info')
            return redirect(url_for("cms.edit_topic_page", slug=page.meta.uri))
    return render_template("cms/new_topic_page.html", form=form, pages=pages)


@cms_blueprint.route('/<topic>/<subtopic>/measure/new', methods=['GET', 'POST'])
@login_required
def create_measure_page(topic, subtopic):
    pages = page_service.get_pages()
    topic_page = page_service.get_page(topic)
    subtopic_page = page_service.get_page(subtopic)
    form = MeasurePageForm()
    if request.method == 'POST':
        form = MeasurePageForm(request.form)
        if form.validate():
            page = page_service.create_page(page_type='measure', parent=topic_page.meta.guid, data=form.data)
            message = 'Created page {}'.format(page.title)
            flash(message, 'info')
            return redirect(url_for("cms.edit_measure_page",
                                    topic=topic_page.meta.guid,
                                    subtopic=subtopic_page.meta.guid,
                                    measure=page.meta.guid))
        else:
            print(form.errors)
    return render_template("cms/new_measure_page.html",
                           form=form,
                           pages=pages,
                           topic=topic_page,
                           subtopic=subtopic_page)


@cms_blueprint.route('/<topic>/edit', methods=['GET', 'POST'])
@login_required
def edit_topic_page(topic):
    try:
        page = page_service.get_page(topic)
    except PageNotFoundException:
        abort(404)

    form = PageForm(obj=page)
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            page_service.update_page(page, data=form.data)
            message = 'Updated page {}'.format(page.title)
            flash(message, 'info')

    current_status = page.meta.status
    available_actions = page.available_actions()
    if 'APPROVE' in available_actions:
        numerical_status = page.publish_status(numerical=True)
        approval_state = publish_status.inv[numerical_status + 1]

    pages = page_service.get_pages()

    context = {
        'form': form,
        'slug': topic,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        'pages': pages
    }

    return render_template("cms/edit_topic_page.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/edit', methods=['GET', 'POST'])
@login_required
def edit_measure_page(topic, subtopic, measure):
    try:
        subtopic_page = page_service.get_page(subtopic)
        topic_page = page_service.get_page(topic)
        page = page_service.get_page(measure)

    except PageNotFoundException:
        abort(404)

    form = MeasurePageForm(obj=page)
    if request.method == 'POST':
        form = MeasurePageForm(request.form)
        if form.validate():
            page_service.update_page(page, data=form.data)
            message = 'Updated page {}'.format(page.title)
            flash(message, 'info')
        else:
            print("NOT VALIDATED")
            print(form.errors)

    current_status = page.meta.status
    available_actions = page.available_actions()
    if 'APPROVE' in available_actions:
        numerical_status = page.publish_status(numerical=True)
        approval_state = publish_status.inv[numerical_status + 1]

    pages = page_service.get_pages()
    context = {
        'form': form,
        'topic': topic_page,
        'subtopic': subtopic_page,
        'measure': page,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        'pages': pages
    }

    return render_template("cms/edit_measure_page.html", **context)


@cms_blueprint.route('/<topic>')
@login_required
def topic_overview(topic):
    try:
        page = page_service.get_page(topic)
    except PageNotFoundException:
        abort(404)

    pages = page_service.get_pages()
    topic_page = [p for p in pages if str(p) == page.guid][0]
    children = pages[topic_page]

    context = {'page': page,
               'children': children}
    return render_template("cms/topic_overview.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>')
@login_required
def subtopic_overview(topic, subtopic):
    try:
        page = page_service.get_page(subtopic)
    except PageNotFoundException:
        abort(404)

    pages = page_service.get_pages()
    for item in pages.items():
        subtopics = item[1]
        try:
            subtopic_page = [p for p in subtopics if str(p) == page.guid][0]
            children = pages[item[0]][subtopic_page]
            topic_page = item[0]
        except IndexError:
            pass

    context = {'page': page,
               'topic': topic_page,
               'children': children}
    return render_template("cms/subtopic_overview.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/upload', methods=['POST'])
@login_required
def upload_file(topic, subtopic, measure):
    file = request.files['file']
    if file.filename == '':
        return json.dumps({'status': 'BAD REQUEST'}), 400
    else:
        page = page_service.get_page(measure)
        page_service.upload_data(page, file)
        return json.dumps({'status': 'OK', 'file': file.filename}), 200


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/publish')
@login_required
def publish_page(measure):
    page = page_service.next_state(measure)
    status = page.meta.status.replace('_', ' ').title()
    message = '"{}" sent to {}'.format(page.title, status)
    flash(message, 'info')
    return redirect(url_for("cms.edit_measure_page", slug=page.meta.uri))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/reject')
@login_required
def reject_page(topic, subtopic, measure):
    page = page_service.reject_page(measure)
    return redirect(url_for("cms.edit_measure_page", topic=topic, subtopic=subtopic, measure=measure))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/create_chart')
@login_required
def create_chart(topic, subtopic, measure, dimension):
    context = {'topic_slug': topic,
               'measure_slug': measure,
               'dimension_slug': dimension,
               'reload_settings': page_service.reload_chart(measure, dimension)}
    return render_template("cms/create_chart.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<dimension>/save_chart', methods=["POST"])
@login_required
def save_chart_to_page(topic, subtopic, measure, dimension):
    chart_json = request.json
    page = page_service.get_page(measure)

    try:
        page_service.get_dimension(page, dimension)
    except DimensionNotFoundException:
        page_service.create_dimension(page=page, title=dimension)

    page_service.update_dimension(page, dimension, {'chart': chart_json['chartObject']})
    page_service.update_chart_source_data(page, dimension, chart_json['source'])
    page_service.save_page(page)
    return 'OK', 200


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/page', methods=['GET'])
@login_required
def get_measure_page(topic, subtopic, measure):
    try:
        page = page_service.get_page(measure)
        return page.to_json(), 200
    except(PageNotFoundException):
        return json.dumps({}), 404
