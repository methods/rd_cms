import json

from copy import deepcopy
from flask import (
    redirect,
    render_template,
    request,
    url_for,
    abort,
    flash,
    current_app,
    jsonify
)

from flask_login import login_required
from werkzeug.datastructures import CombinedMultiDict

from application.cms import cms_blueprint

from application.cms.exceptions import (
    PageNotFoundException,
    DimensionNotFoundException,
    DimensionAlreadyExists,
    PageExistsException,
    UploadNotFoundException, UpdateAlreadyExists)

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
from application.utils import get_bool, internal_user_required


@cms_blueprint.route('/')
@internal_user_required
@login_required
def index():
    pages = page_service.get_topics()
    return render_template('cms/index.html', pages=pages)


@cms_blueprint.route('/overview', methods=['GET'])
@internal_user_required
@login_required
def overview():
    pages = page_service.get_pages_by_type('topic')
    return render_template('cms/overview.html', pages=pages)


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
    if request.method == 'POST':
        form = MeasurePageForm(request.form)
        try:
            if form.validate():
                page = page_service.create_page(page_type='measure',
                                                parent=subtopic_page,
                                                data=form.data)

                message = 'created page {}'.format(page.title)
                flash(message, 'info')
                current_app.logger.info(message)
                return redirect(url_for("cms.edit_measure_page",
                                        topic=topic_page.guid,
                                        subtopic=subtopic_page.guid,
                                        measure=page.guid,
                                        version=page.version))
            else:
                flash(form.errors, 'error')
        except PageExistsException as e:
            message = str(e)
            flash(message, 'error')
            current_app.logger.error(message)
            return redirect(url_for("cms.create_measure_page",
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


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/uploads/<upload>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_upload(topic, subtopic, measure, upload):
    try:
        measure_page = page_service.get_page(measure)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        upload_obj = measure_page.get_upload(upload)
    except PageNotFoundException:
        abort(404)
    except UploadNotFoundException:
        abort(404)

    form = UploadForm(obj=upload_obj)

    if request.method == 'POST':
        form = UploadForm(request.form)
        if form.validate():
            page_service.edit_measure_upload(measure=measure_page,
                                             upload=upload_obj,
                                             data=form.data)
            message = 'Updated upload {}'.format(upload_obj.title)
            flash(message, 'info')

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


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/edit', methods=['GET', 'POST'])
@internal_user_required
@login_required
def edit_measure_page(topic, subtopic, measure, version):
    try:
        subtopic_page = page_service.get_page(subtopic)
        topic_page = page_service.get_page(topic)
        page = page_service.get_page_with_version(measure, version)
    except PageNotFoundException:
        abort(404)

    form = MeasurePageForm(obj=page)
    if request.method == 'POST':
        form = MeasurePageForm(request.form)
        if form.validate():
            page_service.update_page(page, data=form.data)
            message = 'Updated page "{}" id: {}'.format(page.title, page.guid)
            current_app.logger.info(message)
            flash(message, 'info')
        else:
            current_app.logger.error('Invalid form')

    current_status = page.status
    available_actions = page.available_actions()
    if 'APPROVE' in available_actions:
        numerical_status = page.publish_status(numerical=True)
        approval_state = publish_status.inv[(numerical_status + 1) % 5]

    context = {
        'form': form,
        'topic': topic_page,
        'subtopic': subtopic_page,
        'measure': page,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
    }

    if _build_is_required(page, request, current_app.config['BETA_PUBLICATION_STATES']):
        context['build'] = True

    return render_template("cms/edit_measure_page.html", **context)


@cms_blueprint.route('/<topic>')
@internal_user_required
@login_required
def topic_overview(topic):
    try:
        page = page_service.get_page(topic)
    except PageNotFoundException:
        abort(404)

    if page.children and page.subtopics is not None:
        ordered_subtopics = []
        for st in page.subtopics:
            for c in page.children:
                if c.guid == st:
                    ordered_subtopics.append(c)

        children = ordered_subtopics if ordered_subtopics else page.children
    else:
        children = []
    context = {'page': page,
               'children': children}
    return render_template("cms/topic_overview.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>')
@internal_user_required
@login_required
def subtopic_overview(topic, subtopic):
    try:
        page = page_service.get_page(subtopic)
    except PageNotFoundException:
        abort(404)

    topic_page = page_service.get_page(topic)

    measures = page_service.get_latest_measures(page)

    context = {'page': page,
               'topic': topic_page,
               'measures': measures}

    return render_template("cms/subtopic_overview.html", **context)


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
            upload = page_service.create_upload(page=measure_page,
                                                upload=f,
                                                title=form.data['title'],
                                                description=form.data['description'],
                                                )

            message = 'uploaded file "{}" to measure "{}"'.format(upload.title, measure)
            current_app.logger.info(message)
            flash(message, 'info')

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


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/publish', methods=['GET'])
@internal_user_required
@login_required
def publish_page(topic, subtopic, measure, version):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        measure_page = page_service.get_page_with_version(measure, version)
    except PageNotFoundException:
        abort(404)

    measure_form = MeasurePageRequiredForm(obj=measure_page)
    dimension_valid = True
    invalid_dimensions = []

    for dimension in measure_page.dimensions:
        dimension_form = DimensionRequiredForm(obj=dimension)
        if not dimension_form.validate():
            invalid_dimensions.append(dimension)

    # Check measure is valid
    if not measure_form.validate() or invalid_dimensions:
        message = 'Cannot submit for review, please see errors below'
        flash(message, 'error')
        if invalid_dimensions:
            for invalid_dimension in invalid_dimensions:
                message = 'Cannot submit for review ' \
                          '<a href="./%s/edit?validate=true">%s</a> dimension is not complete.'\
                          % (invalid_dimension.guid, invalid_dimension.title)
                flash(message, 'error')

        current_status = measure_page.status
        available_actions = measure_page.available_actions()
        if 'APPROVE' in available_actions:
            numerical_status = measure_page.publish_status(numerical=True)
            approval_state = publish_status.inv[numerical_status + 1]

        context = {
            'form': measure_form,
            'topic': topic_page,
            'subtopic': subtopic_page,
            'measure': measure_page,
            'status': current_status,
            'available_actions': available_actions,
            'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        }

        return render_template("cms/edit_measure_page.html", **context)

    message = page_service.next_state(measure_page)
    flash(message, 'info')

    build = measure_page.eligible_for_build(current_app.config['BETA_PUBLICATION_STATES'])
    if build:
        return redirect(url_for("cms.edit_measure_page",
                                topic=topic,
                                subtopic=subtopic,
                                measure=measure,
                                build=build,
                                version=version))
    else:
        return redirect(url_for("cms.edit_measure_page",
                                topic=topic,
                                subtopic=subtopic,
                                measure=measure,
                                version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/reject')
@internal_user_required
@login_required
def reject_page(topic, subtopic, measure, version):
    message = page_service.reject_page(measure, version)
    flash(message, 'info')
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/unpublish')
@internal_user_required
@login_required
def unpublish_page(topic, subtopic, measure, version):
    message = page_service.unpublish(measure, version)
    flash(message, 'info')
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
                                                          summary=form.data['summary'],
                                                          suppression_rules=form.data['suppression_rules'],
                                                          disclosure_control=form.data['disclosure_control'],
                                                          type_of_statistic=form.data['type_of_statistic'],
                                                          location=form.data['location'],
                                                          source=form.data['source'])
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
               "create": False,
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


# TODO give this the same treatment as save chart to page
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


@internal_user_required
@login_required
@cms_blueprint.route('/build-static-site', methods=['GET'])
def build_static_site():
    from application.sitebuilder.build import do_it
    do_it(current_app)
    return 'OK', 200


def _build_is_required(page, req, beta_publication_states):
    if page.status == 'UNPUBLISHED':
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
        return redirect(url_for('cms.subtopic_overview', topic=topic, subtopic=subtopic))
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
            return redirect(url_for("cms.list_measure_page_versions",
                                    topic=topic,
                                    subtopic=subtopic,
                                    measure=measure))
        except UpdateAlreadyExists as e:
            message = 'Version %s of page %s is already being updated' % (version, measure)
            flash(message, 'error')
            return redirect(url_for('cms.new_version',
                                    topic=topic, subtopic=subtopic,
                                    measure=measure,
                                    version=measure.version,
                                    form=form))

    return render_template('cms/create_new_version.html',
                           topic=topic_page,
                           subtopic=subtopic_page,
                           measure=measure_page,
                           form=form)
