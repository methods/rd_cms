from flask import (
    redirect,
    render_template,
    request,
    url_for,
    current_app
)

from flask_login import login_required

from application.cms import cms_blueprint
from application.cms.forms import PageForm
from application.cms.models import Page, Struct


@cms_blueprint.route('/')
@login_required
def index():
    return render_template('cms/index.html')


@cms_blueprint.route('/pages/new', methods=['GET', 'POST'])
@login_required
def create_page():
    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            title = form.data['title']
            page = Page(guid=title, config=current_app.config)
            page.create_new_page(initial_data=form.data)
            return redirect(url_for("cms.edit_page", guid=title))
    return render_template("cms/new_page.html", form=form)


@cms_blueprint.route('/pages/<guid>/edit', methods=['GET', 'POST'])
@login_required
def edit_page(guid):
    # TODO: Currently this page is view only
    # TODO: 404 when page not found
    page = Page(guid=guid, config=current_app.config)
    page_content = page.file_content('page.json')
    page_data = Struct(**page_content)
    form = PageForm(obj=page_data)

    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            page.update_page_data(new_data=form.data)

    context = {
        'form': form,
        'guid': guid,
        'status': page.publish_status()
    }

    return render_template("cms/edit_page.html", **context)


@cms_blueprint.route('/pages/<guid>/publish')
@login_required
def publish_page(guid):
    page = Page(guid=guid, config=current_app.config)
    page.publish()
    return redirect(url_for("cms.edit_page", guid=guid))


@cms_blueprint.route('/pages/<guid>/reject')
@login_required
def reject_page(guid):
    page = Page(guid=guid, config=current_app.config)
    page.reject()
    return redirect(url_for("cms.edit_page", guid=guid))
