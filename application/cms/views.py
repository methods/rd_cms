import json

from flask import (
    redirect,
    render_template,
    request,
    url_for,
    abort,
    flash,
    current_app,
    jsonify,
    session
)

from flask_login import login_required, current_user
from werkzeug.datastructures import CombinedMultiDict

from application.cms import cms_blueprint

from application.cms.exceptions import (
    PageNotFoundException,
    DimensionNotFoundException,
    DimensionAlreadyExists,
    PageExistsException,
    UploadNotFoundException,
    UpdateAlreadyExists,
    UploadCheckError,
    StaleUpdateException
)

from application.cms.forms import (
    MeasurePageForm,
    DimensionForm,
    MeasurePageRequiredForm,
    DimensionRequiredForm,
    UploadForm,
    NewVersionForm
)

from application.cms.models import publish_status
from application.cms.page_service import page_service
from application.utils import get_bool, internal_user_required, admin_required
from application.sitebuilder import build_service


@cms_blueprint.route('/')
@internal_user_required
@login_required
def index():
    pages = page_service.get_topics()
    return render_template('cms/index.html', pages=pages)


@cms_blueprint.route('/measures', methods=['GET'])
@internal_user_required
@login_required
def measures():
    pages = page_service.get_pages_by_type('topic')
    return render_template('cms/measures.html', pages=pages)


# Temporary measure page fact
@cms_blueprint.route('/measures/facts-and-figures', methods=['GET'])
@internal_user_required
@login_required
def measure_page_facts_and_figures():
    from application.cms.models import DbPage
    from datetime import date, datetime, timedelta
    import calendar

    measures = DbPage.query.filter(
        DbPage.publication_date.isnot(None),
        DbPage.version == '1.0'
    ).all()

    updates = DbPage.query.filter(
        DbPage.publication_date.isnot(None),
        DbPage.version != '1.0'
    ).all()

    seven_days = timedelta(days=7)
    seven_days_ago = datetime.today() - seven_days
    in_last_week = DbPage.query.filter(
        DbPage.publication_date.isnot(None),
        DbPage.publication_date >= seven_days_ago
    ).all()

    first_publication = DbPage.query.filter(
        DbPage.publication_date.isnot(None)
    ).order_by(DbPage.publication_date.asc()).first()

    data = {'publications': len(measures),
            'updates': len(updates),
            'in_last_week': len(in_last_week),
            'first_publication': first_publication.publication_date}

    measures_by_week = {}

    def month_iterator(start, end):
        current = start
        while current < end:
            yield current
            current += timedelta(days=current.max.day)

    def in_range(week, begin, end=date.today()):
        return any([d for d in week if d >= begin]) and any([d for d in week if d <= end])

    for m in month_iterator(first_publication.publication_date, date.today()):
        c = calendar.Calendar(calendar.MONDAY).monthdatescalendar(m.year, m.month)
        for week in c:
                if in_range(week, first_publication.publication_date):
                    publications = DbPage.query.filter(
                        DbPage.publication_date.isnot(None),
                        DbPage.publication_date >= week[0],
                        DbPage.publication_date <= week[6],
                        DbPage.version == '1.0'
                    ).all()
                    updates = DbPage.query.filter(
                        DbPage.publication_date.isnot(None),
                        DbPage.publication_date >= week[0],
                        DbPage.publication_date <= week[6],
                        DbPage.version != '1.0'
                    ).all()
                    measures_by_week[week[0]] = {'publications': len(publications), 'updates': len(updates)}

    data['measures_by_week'] = measures_by_week

    return render_template('cms/measure_facts_and_figures.html', data=data)


@cms_blueprint.route('/<topic>/<subtopic>/measure/new', methods=['GET', 'POST'])
@internal_user_required
@login_required
def create_measure_page(topic, subtopic):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
    except PageNotFoundException:
        abort(404)
    form = MeasurePageForm()
    if form.validate_on_submit():
        try:
            if form.validate():
                page = page_service.create_page(page_type='measure',
                                                parent=subtopic_page,
                                                data=form.data,
                                                created_by=current_user.email)

                message = 'created page {}'.format(page.title)
                flash(message, 'info')
                current_app.logger.info(message)
                return redirect(url_for("cms.edit_measure_page",
                                        topic=topic_page.guid,
                                        subtopic=subtopic_page.guid,
                                        measure=page.guid,
                                        version=page.version))
        except PageExistsException as e:
            message = str(e)
            flash(message, 'error')
            current_app.logger.error(message)
            return redirect(url_for("cms.create_measure_page",
                                    form=form,
                                    topic=topic,
                                    subtopic=subtopic))

    return render_template("cms/new_measure_page.html",
                           form=form,
                           topic=topic_page,
                           subtopic=subtopic_page)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/uploads/<upload>/delete', methods=['GET'])
@internal_user_required
@login_required
def delete_upload(topic, subtopic, measure, version, upload):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        upload_object = measure_page.get_upload(upload)
    except PageNotFoundException:
        current_app.logger.exception('Page id: {} not found'.format(measure))
        abort(404)
    except UploadNotFoundException:
        current_app.logger.exception('upload id: {} not found'.format(upload))
        abort(404)
    page_service.delete_upload_obj(measure_page, upload_object.guid)

    message = 'Deleted upload {}'.format(upload_object.title)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/uploads/<upload>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_upload(topic, subtopic, measure, version, upload):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        upload_obj = measure_page.get_upload(upload)
    except PageNotFoundException:
        abort(404)
    except UploadNotFoundException:
        abort(404)

    form = UploadForm(obj=upload_obj)

    if request.method == 'POST':
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            f = form.upload.data if form.upload.data else None
            try:
                page_service.edit_upload(measure=measure_page,
                                         upload=upload_obj,
                                         file=f,
                                         data=form.data)
                message = 'Updated upload {}'.format(upload_obj.title)
                flash(message, 'info')
                return redirect(url_for("cms.edit_measure_page",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        version=version))
            except UploadCheckError as e:
                message = 'Error uploading file. {}'.format(str(e))
                current_app.logger.exception(e)
                flash(message, 'error')

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page,
               "upload": upload_obj
               }
    return render_template("cms/edit_upload.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/delete', methods=['GET'])
@internal_user_required
@login_required
def delete_dimension(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    page_service.delete_dimension(measure_page, dimension_object.guid)

    message = 'Deleted dimension {}'.format(dimension_object.title)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


def _diff_updates(form, page):
    from lxml.html.diff import htmldiff
    diffs = {}
    for k, v in form.data.items():
        if hasattr(page, k) and k != 'db_version_id':
            page_value = getattr(page, k)
            if v is not None and page_value is not None:
                diff = htmldiff(page_value.rstrip(), v.rstrip())
                if '<ins>' in diff or '<del>' in diff:
                    getattr(form, k).errors.append('has been updated by %s' % page.last_updated_by)
                    diffs[k] = diff
    form.db_version_id.data = page.db_version_id
    return diffs


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_measure_page(topic, subtopic, measure, version):
    diffs = {}
    try:
        subtopic_page = page_service.get_page(subtopic)
        topic_page = page_service.get_page(topic)
        page = page_service.get_page_with_version(measure, version)
    except PageNotFoundException:
        abort(404)

    form = MeasurePageForm(obj=page)
    saved = False
    if request.method == 'POST':
        form = MeasurePageForm(request.form)
        if form.validate():
            try:
                page_service.update_page(page, data=form.data, last_updated_by=current_user.email)
                message = 'Updated page "{}" id: {}'.format(page.title, page.guid)
                current_app.logger.info(message)
                flash(message, 'info')
                saved = True
            except PageExistsException as e:
                current_app.logger.info(e)
                flash(str(e), 'error')
                form.title.data = page.title
            except StaleUpdateException as e:
                current_app.logger.error(e)
                diffs = _diff_updates(form, page)
                if diffs:
                    flash('Your update will overwrite the latest content. Resolve the conflicts below', 'error')
                else:
                    flash('Your update will overwrite the latest content. Reload this page', 'error')
        else:
            current_app.logger.error('Invalid form')

    current_status = page.status
    available_actions = page.available_actions()
    if 'APPROVE' in available_actions:
        numerical_status = page.publish_status(numerical=True)
        approval_state = publish_status.inv[(numerical_status + 1) % 6]

    if saved and 'save-and-review' in request.form:
        return redirect(url_for('cms.send_to_review',
                                topic=topic,
                                subtopic=subtopic,
                                measure=page.guid,
                                version=page.version))
    elif saved:
        return redirect(url_for('cms.edit_measure_page',
                                topic=topic,
                                subtopic=subtopic,
                                measure=page.guid,
                                version=page.version))

    context = {
        'form': form,
        'topic': topic_page,
        'subtopic': subtopic_page,
        'measure': page,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        'diffs': diffs
    }

    return render_template("cms/edit_measure_page.html", **context)


@cms_blueprint.route('/<topic>')
@internal_user_required
@login_required
def topic(topic):
    try:
        page = page_service.get_page(topic)
    except PageNotFoundException:
        abort(404)

    context = {'page': page,
               'children': page.children}
    return render_template("cms/topic.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>')
@internal_user_required
@login_required
def subtopic(topic, subtopic):
    try:
        page = page_service.get_page(subtopic)
    except PageNotFoundException:
        abort(404)

    topic_page = page_service.get_page(topic)

    measures = page_service.get_latest_measures(page)

    context = {'page': page,
               'topic': topic_page,
               'measures': measures}

    return render_template("cms/subtopic.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/upload', methods=['GET', 'POST'])
@internal_user_required
@login_required
def create_upload(topic, subtopic, measure, version):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        measure_page = page_service.get_page_with_version(measure, version)
    except PageNotFoundException:
        abort(404)

    form = UploadForm()
    if request.method == 'POST':
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            f = form.upload.data
            try:
                upload = page_service.create_upload(page=measure_page,
                                                    upload=f,
                                                    title=form.data['title'],
                                                    description=form.data['description'],
                                                    )

                message = 'uploaded file "{}" to measure "{}"'.format(upload.title, measure)
                current_app.logger.info(message)
                flash(message, 'info')

            except UploadCheckError as e:
                message = 'Error uploading file. {}'.format(str(e))
                current_app.logger.exception(e)
                flash(message, 'error')
                context = {"form": form,
                           "topic": topic_page,
                           "subtopic": subtopic_page,
                           "measure": measure_page
                           }
                return render_template("cms/create_upload.html", **context)

            return redirect(url_for("cms.edit_measure_page",
                                    topic=topic,
                                    subtopic=subtopic,
                                    measure=measure,
                                    version=version))

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page
               }
    return render_template("cms/create_upload.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/send-to-review', methods=['GET'])
@internal_user_required
@login_required
def send_to_review(topic, subtopic, measure, version):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        measure_page = page_service.get_page_with_version(measure, version)
    except PageNotFoundException:
        abort(404)

    # in case user tries to directly GET this page
    if measure_page.status == 'DEPARTMENT_REVIEW':
        abort(400)

    measure_form = MeasurePageRequiredForm(obj=measure_page, meta={'csrf': False})
    invalid_dimensions = []

    for dimension in measure_page.dimensions:
        dimension_form = DimensionRequiredForm(obj=dimension, meta={'csrf': False})
        if not dimension_form.validate():
            invalid_dimensions.append(dimension)

    if not measure_form.validate() or invalid_dimensions:
        # don't need to show user page has been saved when
        # required field validation failed.
        session.pop('_flashes', None)
        form = MeasurePageRequiredForm(obj=measure_page)
        for key, val in measure_form.errors.items():
            form.errors[key] = val
            field = getattr(form, key)
            field.errors = val
            setattr(form, key, field)

        message = 'Cannot submit for review, please see errors below'
        flash(message, 'error')
        if invalid_dimensions:
            for invalid_dimension in invalid_dimensions:
                message = 'Cannot submit for review ' \
                          '<a href="./%s/edit?validate=true">%s</a> dimension is not complete.'\
                          % (invalid_dimension.guid, invalid_dimension.title)
                flash(message, 'dimension-error')

        current_status = measure_page.status
        available_actions = measure_page.available_actions()
        if 'APPROVE' in available_actions:
            numerical_status = measure_page.publish_status(numerical=True)
            approval_state = publish_status.inv[numerical_status + 1]

        context = {
            'form': form,
            'topic': topic_page,
            'subtopic': subtopic_page,
            'measure': measure_page,
            'status': current_status,
            'available_actions': available_actions,
            'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        }

        return render_template("cms/edit_measure_page.html", **context)

    message = page_service.next_state(measure_page, updated_by=current_user.email)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/publish', methods=['GET'])
@internal_user_required
@admin_required
@login_required
def publish(topic, subtopic, measure, version):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        if measure_page.status != 'DEPARTMENT_REVIEW':
            abort(400)
        message = page_service.next_state(measure_page, current_user.email)
        current_app.logger.info(message)
        _build_if_necessary(measure_page)
        flash(message, 'info')
        return redirect(url_for("cms.edit_measure_page",
                                topic=topic,
                                subtopic=subtopic,
                                measure=measure,
                                version=version))
    except PageNotFoundException:
        abort(404)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/reject')
@internal_user_required
@login_required
def reject_page(topic, subtopic, measure, version):
    message = page_service.reject_page(measure, version)
    flash(message, 'info')
    current_app.logger.info(message)
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/unpublish')
@internal_user_required
@admin_required
@login_required
def unpublish_page(topic, subtopic, measure, version):
    page, message = page_service.unpublish(measure, version, current_user.email)
    _build_if_necessary(page)
    flash(message, 'info')
    current_app.logger.info(message)
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/draft')
@internal_user_required
@login_required
def send_page_to_draft(topic, subtopic, measure, version):
    message = page_service.send_page_to_draft(measure, version)
    flash(message, 'info')
    current_app.logger.info(message)
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/dimension/new', methods=['GET', 'POST'])
@internal_user_required
@login_required
def create_dimension(topic, subtopic, measure, version):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        measure_page = page_service.get_page_with_version(measure, version)
    except PageNotFoundException:
        abort(404)

    form = DimensionForm()
    if request.method == 'POST':
        form = DimensionForm(request.form)

        messages = []
        if form.validate():
            try:
                dimension = page_service.create_dimension(page=measure_page,
                                                          title=form.data['title'],
                                                          time_period=form.data['time_period'],
                                                          summary=form.data['summary'])
                message = 'Created dimension "{}"'.format(dimension.title)
                flash(message, 'info')
                current_app.logger.info(message)
                return redirect(url_for("cms.edit_dimension",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        version=version,
                                        dimension=dimension.guid))
            except(DimensionAlreadyExists):
                message = 'Dimension with title "{}" already exists'.format(form.data['title'])
                flash(message, 'error')
                current_app.logger.error(message)
                return redirect(url_for("cms.create_dimension",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        version=version,
                                        messages=[{'message': 'Dimension with code %s already exists'
                                                              % form.data['title']}]))
        else:
            flash('Please complete all fields in the form', 'error')

    context = {"form": form,
               "create": True,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page
               }
    return render_template("cms/create_dimension.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_dimension(topic, subtopic, measure, dimension, version):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        current_app.logger.exception('Page id {} not found'.format(measure))
        abort(404)
    except DimensionNotFoundException:
        current_app.logger.exception('Dimension id {} of page id {} not found'.format(dimension, measure))
        abort(404)

    validate = request.args.get('validate')
    if validate:
        form = DimensionRequiredForm(obj=dimension_object)
        if not form.validate():
            message = "Cannot submit for review, please see errors below"
            flash(message, 'error')
    else:
        form = DimensionForm(obj=dimension_object)

    if request.method == 'POST':
        form = DimensionForm(request.form)
        if form.validate():
            page_service.update_dimension(dimension=dimension_object,
                                          data=form.data)
            message = 'Updated dimension {}'.format(dimension)
            flash(message, 'info')

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page,
               "dimension": dimension_object
               }
    return render_template("cms/edit_dimension.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/create_chart')
@internal_user_required
@login_required
def create_chart(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_object.to_dict(),
               'simple_chart_builder': current_app.config['SIMPLE_CHART_BUILDER']}

    return render_template("cms/create_chart.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/create_table')
@internal_user_required
@login_required
def create_table(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_object.to_dict()}

    return render_template("cms/create_table.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/save_chart', methods=["POST"])
@internal_user_required
@login_required
def save_chart_to_page(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    chart_json = request.json

    page_service.update_measure_dimension(measure_page, dimension_object, chart_json)

    message = 'updated chart on dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/delete_chart')
@internal_user_required
@login_required
def delete_chart(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    page_service.delete_chart(dimension_object)

    message = 'deleted chart from dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_dimension",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version,
                            dimension=dimension_object.guid))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/save_table', methods=["POST"])
@internal_user_required
@login_required
def save_table_to_page(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    table_json = request.json

    page_service.update_measure_dimension(measure_page, dimension_object, table_json)

    message = 'updated table on dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/delete_table')
@internal_user_required
@login_required
def delete_table(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    page_service.delete_table(dimension_object)

    message = 'deleted table from dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_dimension",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version,
                            dimension=dimension_object.guid))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/page', methods=['GET'])
@internal_user_required
@login_required
def get_measure_page(topic, subtopic, measure, version):
    try:
        page = page_service.get_page_with_version(measure, version)
        return page.page_json, 200
    except PageNotFoundException:
        return json.dumps({}), 404


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/uploads', methods=['GET'])
@internal_user_required
@login_required
def get_measure_page_uploads(topic, subtopic, measure, version):
    try:
        page = page_service.get_page_with_version(measure, version)
        uploads = page_service.get_page_uploads(page)
        return json.dumps({'uploads': uploads}), 200
    except PageNotFoundException:
        return json.dumps({}), 404


def _build_is_required(page, req, beta_publication_states):
    if page.status == 'UNPUBLISH':
        return True
    if get_bool(req.args.get('build')) and page.eligible_for_build(beta_publication_states):
        return True
    return False


@cms_blueprint.route('/data_processor', methods=['POST'])
@internal_user_required
@login_required
def process_input_data():
    if current_app.harmoniser:
        request_json = request.json
        return_data = current_app.harmoniser.process_data(request_json['data'])
        return json.dumps({'data': return_data}), 200
    else:
        return json.dumps(request.json), 200


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/set-dimension-order', methods=['POST'])
@internal_user_required
@login_required
def set_dimension_order(topic, subtopic, measure):
    dimensions = request.json.get('dimensions', [])
    try:
        page_service.set_dimension_positions(dimensions)
        return json.dumps({'status': 'OK', 'status_code': 200}), 200
    except Exception as e:
        return json.dumps({'status': 'INTERNAL SERVER ERROR', 'status_code': 500}), 500


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/versions')
@internal_user_required
@login_required
def list_measure_page_versions(topic, subtopic, measure):
    topic_page = page_service.get_page(topic)
    subtopic_page = page_service.get_page(subtopic)
    measures = page_service.get_measure_page_versions(subtopic, measure)
    measures.sort(reverse=True)
    if not measures:
        return redirect(url_for('cms.subtopic', topic=topic, subtopic=subtopic))
    measure_title = measures[0].title if measures else ''
    return render_template('cms/measure_page_versions.html',
                           topic=topic_page,
                           subtopic=subtopic_page,
                           measures=measures,
                           measure_title=measure_title)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/delete')
@internal_user_required
@login_required
def delete_measure_page(topic, subtopic, measure, version):
    try:
        page_service.delete_measure_page(measure, version)
        message = 'Deleted version %s' % version
        flash(message)
        return redirect(url_for('cms.list_measure_page_versions', topic=topic, subtopic=subtopic, measure=measure))
    except PageNotFoundException:
        abort(404)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/new-version', methods=['GET', 'POST'])
@internal_user_required
@login_required
def new_version(topic, subtopic, measure, version):
    topic_page = page_service.get_page(topic)
    subtopic_page = page_service.get_page(subtopic)
    measure_page = page_service.get_page_with_version(measure, version)
    form = NewVersionForm()
    if form.validate_on_submit():
        version_type = form.data['version_type']
        try:
            page = page_service.create_copy(measure, version, version_type)
            message = 'Added a new %s version %s' % (version_type, page.version)
            flash(message)
            return redirect(url_for("cms.edit_measure_page",
                                    topic=topic_page.guid,
                                    subtopic=subtopic_page.guid,
                                    measure=page.guid,
                                    version=page.version))
        except UpdateAlreadyExists as e:
            message = 'Version %s of page %s is already being updated' % (version, measure)
            flash(message, 'error')
            return redirect(url_for('cms.new_version',
                                    topic=topic,
                                    subtopic=subtopic,
                                    measure=measure,
                                    version=measure.version,
                                    form=form))

    return render_template('cms/create_new_version.html',
                           topic=topic_page,
                           subtopic=subtopic_page,
                           measure=measure_page,
                           form=form)


def _build_if_necessary(page):
    if page.status == 'UNPUBLISH':
        build_service.request_build()
    elif page.eligible_for_build(current_app.config['PUBLICATION_STATES']):
        page_service.mark_page_published(page)
        build_service.request_build()
