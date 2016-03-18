__author__ = 'pgilmore'

from django.db import connections

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

import os
import csv
import time
import chardet

from matching.models import Spreadsheets
from matching.models import Users


class TwisterDataUploader():

    def __init__(self):

        # The column headers from the input csv data (or file)
        self.csv_data = list()
        self.column_headers = list()

        #file system for storing files
        if os.path.isdir(settings.BASE_DIR + "/twister/templates/twister/"):
            pass
        else:
            #os.mkdir(settings.MEDIA_ROOT + "twister/") #use this one, but the below is a quick test
            os.mkdir(settings.BASE_DIR + "/twister/templates/twister/")

        self.file_system = FileSystemStorage(location=settings.BASE_DIR + "/twister/templates/twister/")

    def get_csv_data_from_db(self, spreadsheet_id):

        # retrieve data associated with a given spreadsheet_id
        spreadsheet_result = list(Spreadsheets.objects.using('pa_io').filter(spreadsheet_id=spreadsheet_id).values_list('data', 'encoding_method'))

        csv_data = spreadsheet_result[0][0]
        encoding_method = spreadsheet_result[0][1]

        # encode from unicode to str
        csv_data = csv_data.encode(encoding_method)

        # next, we split the data using newlines as a delimiter
        csv_data_list = csv_data.split('\n')

        # get the data
        row_string_list = [one_row for index, one_row in enumerate(csv_data_list) if index > 0]

        # for each element of data_list, split it by \t, since adjacent cells are separated by tabs
        csv_data = [one_row_string.split('\t') for one_row_string in row_string_list]

        # get the header
        header_str = csv_data_list[0]

        # turn header into a list of strings
        header_list = header_str.split('\t')

        # assign header_str and csv_data to their corresponding fields
        self.column_headers = header_list
        self.csv_data = csv_data

        return csv_data

    def insert_csv_data_into_db(self, file_name, company_id, user_id, spreadsheet_id=None, usage=1):

        #get the headers and data as a single string, where each row is separated by a newline character
        csv_headers = self.column_headers
        csv_data = self.csv_data

        headers_formatted = '\t'.join(csv_headers)

        data_flattened = ['\t'.join(onerow) for onerow in csv_data]
        data_formatted = '\n'.join(data_flattened)
        final_data = headers_formatted + '\n' + data_formatted
        final_data = final_data.replace("\'", "\'\'")

        #detect character encoding of csv data
        encoding = chardet.detect(final_data)

        encoding_method = encoding['encoding']
        #encoding_confidence = encoding['confidence']

        spreadsheet_date = time.strftime('%Y-%m-%d %H:%M:%S')

        if spreadsheet_id is not None:

            spreadsheet_object = Spreadsheets.objects.using('pa_io').filter(spreadsheet_id=spreadsheet_id)[0]
            spreadsheet_object.data = final_data
            spreadsheet_object.spreadsheet_name = file_name
            spreadsheet_object.last_updated_by = user_id
            spreadsheet_object.last_updated_date = spreadsheet_date
            spreadsheet_object.save(using='pa_io')
        else:
            final_data = final_data.decode(encoding_method)
            spreadsheet_id = Spreadsheets.objects.using('pa_io').latest('spreadsheet_id').spreadsheet_id + 1

            spreadsheet_object = Spreadsheets()
            spreadsheet_object.company_id = company_id
            spreadsheet_object.user_id = user_id
            spreadsheet_object.spreadsheet_name = file_name
            spreadsheet_object.usage = usage
            spreadsheet_object.data = final_data
            spreadsheet_object.share_type = 2
            spreadsheet_object.created_by = user_id
            spreadsheet_object.created_date = spreadsheet_date
            spreadsheet_object.last_updated_by = user_id
            spreadsheet_object.last_updated_date = spreadsheet_date
            spreadsheet_object.encoding_method = encoding_method

            flag_saved = False
            while not flag_saved:
                try:
                    spreadsheet_object.spreadsheet_id = spreadsheet_id
                    spreadsheet_object.save(using='pa_io')

                    flag_saved = True
                except IntegrityError:
                    try:
                        spreadsheet_id = Spreadsheets.objects.using('pa_io').latest('spreadsheet_id').spreadsheet_id + 1
                    except ObjectDoesNotExist:
                        spreadsheet_id = 1

        return spreadsheet_id

    def read_spreadsheet_data(self, data):

        #clear self.csv_data value from previous uploads before we start reading
        self.csv_data = []

        row_list = data.split('\n')

        for index, row in enumerate(row_list):

            #replace tabs with commas
            row = row.replace('\t',',')
            row = row.replace('\r','')

            #surround each field with single quotes
            row_fields_list = row.split(',')
            row_fields_list = [field.encode('utf-8') for field in row_fields_list]

            #if line 1 in data, it is the header
            if index == 0:
                self.column_headers = row_fields_list
            else:
                if row:
                    self.csv_data.append(row_fields_list)

    def read_csv_data_from_file(self, filename):

        #clear self.csv_data value from previous uploads before we start reading
        self.csv_data = []

        try:
            file_path = self.file_system.path(filename)
        except NotImplementedError:
            raise Exception('File not found for reading')

        with open(file_path, 'rb') as file_handle:
            file_reader = csv.reader(file_handle)
            count = 0
            for row in file_reader:
                if count == 0:
                    count = 1
                    self.column_headers = row
                else:
                    if row:
                        self.csv_data.append(row)