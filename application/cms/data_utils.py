from tempfile import TemporaryDirectory

import pandas as pd
import numpy as np

import csv
import os

from flask import current_app


class DataProcessor:
    """
    Data processor takes a page, iterates through it's source folder, and process the files fit for publication
    """

    def __init__(self):
        self.file_service = current_app.file_service

    """
    main public process
    """
    def process_files(self, page):

        self.process_page_level_files(page)

    """
    setup directories for the page
    """
    def setup_directories(self, page_file_dir):
        data_dir = '%s/data' % page_file_dir

        try:
            os.removedirs(data_dir)
        except FileNotFoundError:
            pass

        os.mkdir(data_dir)

    """
    Process files at the measure level
    (this is as opposed to files at the dimension level)
    """
    def process_page_level_files(self, page):
        page_system = self.file_service.page_system(page)
        # delete existing processed files
        data_files = page_system.list_files(fs_path='data')
        for file_name in data_files:
            page_system.delete(fs_path='data/%s' % file_name)

        # process all source files
        source_files = page_system.list_files('source')
        for path in source_files:
            source_path = 'source/%s' % path
            data_path = 'data/%s' % path
            if self.do_process_as_csv(source_path):
                CsvProcessor(self.file_service).process_page_level_csv(input_path=source_path,
                                                                       output_path=data_path,
                                                                       page=page)
            else:
                with TemporaryDirectory() as tmp_dir:
                    source_tmp = '%s/source.tmp' % tmp_dir
                    page_system.read(fs_path=source_path, local_path=source_tmp)
                    page_system.write(local_path=source_tmp, fs_path=data_path)

    """
    check whether to process as a csv
    """
    def do_process_as_csv(self, path):
        filename, file_extension = os.path.splitext(path)
        return file_extension == '.csv'


class CsvProcessor:
    def __init__(self, file_system_service):
        self.file_service = file_system_service

    def process_page_level_csv(self, input_path, output_path, page):
        MetadataProcessor(self.file_service).process_page_level_file(input_path=input_path,
                                                                     output_path=output_path,
                                                                     page=page)


class MetadataProcessor:
    """
    Processor to add metadata to data documents
    """
    def __init__(self, file_system_service):
        self.file_service = file_system_service

    """
    public process for adding metadata at page level documents
    """
    def process_page_level_file(self, input_path, output_path, page):
        page_system = self.file_service.page_system(page)

        with TemporaryDirectory() as tmp_dir:
            source_path = '%s/source.tmp' % tmp_dir
            page_system.read(fs_path=input_path, local_path=source_path)

            data_path = '%s/data.tmp' % tmp_dir
            with open(data_path, 'w') as output_file:
                writer = csv.writer(output_file)
                self.append_metadata_rows(page, writer)
                self.append_csv_rows(source_path, writer)

            page_system.write(local_path=data_path, fs_path=output_path)

    """
    add the metadata to a csv writer
    """
    def append_metadata_rows(self, page, writer):
        metadata = [['Title:', page.title],
                    ['Time period:', page.time_covered],
                    ['Location:', page.geographic_coverage],
                    ['Source:', page.source_text],
                    ['Department:', page.department_source],
                    ['Last update:', page.last_update_date],
                    ['', ''],
                    ['', '']]
        [writer.writerow(row) for row in metadata]

    """
    stream a second csv from an input stream to a csv writer
    """
    def append_csv_rows(self, input_path, writer):
        with open(input_path, encoding="latin-1") as input_file:
            reader = csv.reader(input_file)
            [writer.writerow(row) for row in reader]

    """
    public process for adding metadata at dimension level
    """
    def process_dimension_level_file(self, input_path, output_path, page, dimension):
        pass


class Harmoniser:
    default_sort_value = 800
    default_ethnicity_columns = ['ethnicity', 'ethnic group']
    default_ethnicity_type_columns = ['ethnicity type', 'ethnicity_type', 'ethnicity-type']

    """
    Harmoniser adds four fields to an ethnicity data set.
    Label                   A harmonised version of the ethnicity name
    Parent-child label      A harmonised version of ethnicity name including the parent name
    Parent                  The name of the ethnicity's parent
    Sort                    An Integer

    Using these four fields we can explore more advanced data options

    Harmoniser relies on keeping a csv up to date with appropriate values for data being used on the platform
    """
    def __init__(self, lookup_file):
        self.lookup = pd.read_csv(lookup_file, header=0)
        self.lookup.fillna('')

    def process_data(self, data, ethnicity_name='', ethnicity_type_name=''):
        headers = data.pop(0)
        try:
            if ethnicity_name != '':
                ethnicity_index = self.find_column(headers, [ethnicity_name])
            else:
                ethnicity_index = self.find_column(headers, self.default_ethnicity_columns)
        except ValueError:
            data.insert(0, headers)
            return data

        try:
            if ethnicity_type_name != '':
                ethnicity_type_index = self.find_column(headers, [ethnicity_type_name])
            else:
                ethnicity_type_index = self.find_column(headers, self.default_ethnicity_type_columns)
        except ValueError:
            # default ethnicity type index to use the ethnicity column (essentially ignore ethnicity types)
            ethnicity_type_index = ethnicity_index

        self.append_columns(data, ethnicity_column=ethnicity_index, ethnicity_type_column=ethnicity_type_index)
        headers.extend(self.lookup.columns[2:])
        data.insert(0, headers)

        return data

    def find_column(self, headers, column_names):
        lower_headers = [h.lower() for h in headers]
        for column_name in column_names:
            try:
                index = lower_headers.index(column_name.lower())
                return index
            except ValueError:
                pass
        raise ValueError

    def append_columns(self, data, ethnicity_column=0, ethnicity_type_column=1):

        for item in data:
            try:
                filtered = self.lookup[self.lookup['Ethnicity'].str.lower() == item[ethnicity_column].lower()]
                double_filtered = filtered[self.lookup['Ethnicity_type'].str.lower()
                                           == item[ethnicity_type_column].lower()]
                if double_filtered.__len__() > 0:
                    self.append_lookup_values(double_filtered, item)
                elif filtered.__len__() > 0:
                    self.append_lookup_values(filtered, item)
                else:
                    item.extend([''] * (self.lookup.columns.__len__() - 2))
            except IndexError:
                pass

    def append_lookup_values(self, lookup_row, item):
        for i in range(2, lookup_row.iloc[0].values.size):
            self.try_append(lookup_row.iloc[0].values[i], item)

    def try_append(self, value, item):
        try:
            if np.isnan(value):
                item.append('')
            else:
                item.append(np.asscalar(value))
        except TypeError:
            item.append(value)
