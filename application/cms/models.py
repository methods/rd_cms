import json
import os
import shutil

from bidict import bidict
from git import Repo
from slugify import slugify

from application.cms.exceptions import (
    PageExistsException,
    RejectionImpossible,
    AlreadyApproved
)

# The below is a bit odd, but WTForms will only populate a form with an
# object(not an object), this is transitional
# Option 1: Give the page all the attributes of the page.json dict,
# and meta.json (it would be useful to have meta)
# Option 2: Use library to convert dictionary to object in the view

publish_status = bidict(
    REJECTED=0,
    DRAFT=1,
    INTERNAL_REVIEW=2,
    DEPARTMENT_REVIEW=3,
    APPROVED=4
)


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

# TODO split: TopicPage and MeasurementPage and inherit from below
# TODO: YOU CANNOT EDIT REJECTED PAGES AT PRESENT


class Page(object):
    def __init__(self, guid, config):
        self.guid = guid
        self.base_directory = config['BASE_DIRECTORY']
        self.repos_dir = config['REPOS_DIRECTORY']
        self.content_repo = config['CONTENT_REPO']
        self.content_dir = config['CONTENT_DIR']
        # TODO: Could make this fully dynamic with a dict comprehension

        self.repos = {
            'REJECTED': '/'.join((self.repos_dir, '_'.join((self.content_repo, "rejected")))),
            'DRAFT': '/'.join((self.repos_dir, '_'.join((self.content_repo, "draft")))),
            'INTERNAL_REVIEW': '/'.join((self.repos_dir, '_'.join((self.content_repo, "internal-review")))),
            'DEPARTMENT_REVIEW': '/'.join((self.repos_dir, '_'.join((self.content_repo, "department-review")))),
            'APPROVED': '/'.join((self.repos_dir, '_'.join((self.content_repo, "approved")))),
        }

    def create_new_page(self, initial_data=None):
        """
        Has five main functions:
        1. Create the file/dir structure based on cms/page_template
        2. Update the meta.json with anything relevant
        3. Save the initial page.json content
        4. Add the files to the git repo and
        5. TODO: Push repo
        6. You could make this transactional, there are a lof of steps
        :param initial_data: dictionary representation of data to be
        placed in page.json
        :return:
        """
        # Create files
        self.create_page_files()
        # Update meta.json
        # TODO: Update this when we get more fields, currently it is
        # basically a POC for updating meta.json
        updated_meta = {'uri': slugify(self.guid)}
        self.update_meta(updated_meta)

        # Save files contents, it's important at this point for commit history
        if initial_data:
            self.save_content(initial_data)

        # Add to git,
        # TODO, This should use the same mechanism as publish
        git_content_repo = Repo(self.repos['DRAFT'])
        page_directory = '/'.join((self.repos['DRAFT'], self.content_dir, self.guid))
        # Add to git
        try:
            git_content_repo = Repo(self.repos['DRAFT'])
            git_content_repo.index.add([page_directory])
        except Exception as e:
            print("Do nothing for now heroku")
        # Push repo
        # git_content_repo.index.commit("Initial commit for page: {}".format(self.guid)) # noqa

    def create_page_files(self):
        """Copies the contents of page_template to the
        /pages/folder/destination"""
        source = '/'.join((self.base_directory, 'page_template/'))
        destination = '/'.join((self.repos['DRAFT'], self.content_dir, self.guid))

        if os.path.exists(destination):
            raise PageExistsException('This page already exists')
        else:
            # Page can be created
            shutil.copytree(source, destination)

            # TODO: This stuff will apply to measurement pages
            # src_directory = "/".join((destination, "source"))
            # data_directory = "/".join((destination, "data"))
            # # Check directories have been created
            # # if type == "measurement":
            # #     if not os.path.exists(src_directory):
            # #         os.makedirs(src_directory)
            # #     if not os.path.exists(data_directory):
            # #         os.makedirs(data_directory)

    def save_content(self, data):
        """
        Updates the relevant page.json.
        :param data: (dictionary) dictionary of all the data that
        will be stored in page.json (we may later want this
         to do a patch/delta on that data, it would be safer)
        :return: None
        """

        with open('/'.join((self.repos['DRAFT'], self.content_dir, self.guid, 'page.json')), 'w') as page_json:
            json.dump(data, page_json)

    def page_content(self):
        """
        Updates the relevant page.json.
        :param name: (str) name of the page being loaded
        :return: a object containing the contents of page.json
        """
        with open('/'.join((self.repos['DRAFT'], self.content_dir, self.guid, 'page.json'))) as data_file:
            data = json.loads(data_file.read())
        return data

    def update_meta(self, new_data):
        """
        Meta is going to do what content does not, it is going to act
        like a patch request, the meta and content methods
        can be merged into one, at some point.
        :return:
        """
        meta_file = '/'.join((self.repos['DRAFT'], self.content_dir, self.guid, 'meta.json'))
        with open(meta_file) as meta_content:
            file_data = json.loads(meta_content.read())
        for key, value in new_data.items():
            file_data[key] = value
        with open(meta_file, 'w') as meta_content:
            json.dump(file_data, meta_content)

    def meta_content(self):
        """TEMPORARY"""
        meta_file = '/'.join((self.repos['DRAFT'], self.content_dir, self.guid, 'meta.json'))
        with open(meta_file) as meta_content:
            file_data = json.loads(meta_content.read())
        return file_data

    def publish_status(self):
        # TODO: provide numeric or string
        return self.meta_content()['status']

    def add_to_git(self, branch):
        pass

    def publish(self):
        """Sends page to next state"""
        current_status = (self.publish_status()).upper()
        num_status = publish_status[current_status]
        if num_status == 0:
            # TODO: Currently Rejected, status will be updated to INTERNAL REVIEW
            pass
        elif num_status <= 3:
            new_status = publish_status.inv[num_status+1]
            self.update_status(new_status)
        else:
            message = "Page: {} is already approved.".format(self.guid)
            raise AlreadyApproved(message)

    def update_status(self, status):
        """Sets a page to have a specific status in meta,
         should all be called from within this class"""
        # Update meta
        self.update_meta({'status': '{}'.format(status)})

    def add_to_status_store(self, status):
        """"""
        # Check git repo exists

        # Add to correct git branch
        # Check if it exists, if it does delete it (we could delete on reject)
        # Add it & commit it

    def reject(self):
        current_status = (self.publish_status()).upper()
        num_status = publish_status[current_status]
        if num_status in [0, 1, 4]:
            # You can't reject a rejected page,
            # a draft page or a approved page.
            message = "Page {} cannot be rejected a page in state: {}.".format(self.guid, current_status)  # noqa
            raise RejectionImpossible(message)
        self.update_meta({'status': '{}'.format(publish_status.inv[0])})

    def parent(self):
        pass

    def children(self):
        pass
