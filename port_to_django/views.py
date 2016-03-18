from django.shortcuts import render
from django.http import HttpResponse
#borrowed from cloudanalytics to do csv upload form
#from satool import aggtool
from twister.forms import DataEntryForm, RaterConfForm
#PG's libraries first port Twister v.35
#import your libraries
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats as stats
from pandas import Series, DataFrame, ExcelWriter
import pandas as pd
import csv
import string
from datetime import datetime
import sys
#custom classes from twister
from TwisterDataUploader import TwisterDataUploader
#pandas work around related to an alert it sends
pd.set_option('mode.chained_assignment',None)

rata = pd.DataFrame()

# Twister's index is a data visualization of binary numbers swirling like a twister.
#the index template responds to mouse click to send user to user_start

def index(request):
    context = dict()
    
    context ['first_name'] = " Phillip "
    context['last_name'] = " Gilmore "
    #return HttpResponse("The sky grows dark...") ; this is its jsut a direct Response
    return render(request, 'twister/index.html', context)


#user_start.html is the intro instructions, and offering performance data file selector
#to create_new_study, the file selector and submit button form link the submission action to create_new_study
#or to user_start2 "more info" link on the bottom of the html links user to full_docs.html 
def user_start(request):
    context = dict()
    version_now = "scicloud_pg_1.1"   
    context["version_now"] = version_now
    
    data_entry_form = DataEntryForm()
    context['data_entry_form'] = data_entry_form
        
    return render(request, 'twister/user_start.html', context)


#choose the file
def create_new_study(request):
    #assert False
    csv_file = request.FILES['csv_file']
    
    twister_data_uploader = TwisterDataUploader()
    
    with open(twister_data_uploader.file_system.location + "/" + csv_file.name, 'wb+') as destination:
        for chunk in csv_file.chunks():
            destination.write(chunk)

    twister_data_uploader.read_csv_data_from_file(csv_file)
    print twister_data_uploader.column_headers
    
    data = pd.read_csv(twister_data_uploader.file_system.location + "/" + csv_file.name,\
                               index_col=['Ratee Unique ID', 'Rater Unique ID'], \
                               na_values=['NULL','-99', 'N/A', '#N/A', 'blank', 0])   
    
    '''FIRST WE GET AS FAR AS WE CAN WITH DATA MANIPULATION'''
    '''DEDUCE THE NUMBER OF ITEMS FOR MANY IMPORTANT OPERATIONS'''
    #k = int(raw_input("\nHow many items are in the scale? \n\
    #(do not count the final confidence item): "))
    
    #above snippet was originally used to request user input
    #given standard format, the metric columns should be deduced with the following
    
    k_span_start = int()
    k_span_end= int()
    
    for i in range(0,len(data.columns)):    
        if "Ratee Status" in data.columns[i]:
            k_span_start = i + 1
            continue
        if "Based on" in data.columns[i]:
            k_span_end = i
            continue
    
    k = k_span_end - k_span_start
    
    
    '''COMPUTING STANDARD ROW-WISE STATISTICS'''
    
    start_item_column = k_span_start
    
    data['Item Avg'] = data.ix[:,start_item_column:(start_item_column+k)].mean(axis=1,skipna=True)
    data['Item Count'] = data.ix[:,start_item_column:(start_item_column+k)].count(axis=1)
    data['Item Median'] = data.ix[:,start_item_column:(start_item_column+k)].median(axis=1,skipna=True)
    data['Item SD.s'] = data.ix[:,start_item_column:(start_item_column+k)].std(axis=1,skipna=True)
    data['Item Min'] = data.ix[:,start_item_column:(start_item_column+k)].min(axis=1,skipna=True)
    data['Item Max'] = data.ix[:,start_item_column:(start_item_column+k)].max(axis=1,skipna=True)
        
    
    '''INSERTING A RANDOM ID AND SETTING IT AS THE INDEX'''
    
    data['Random ID'] = range(1,len(data)+1)
    data['Random ID_index'] = data['Random ID']
    
    data = data.reset_index()
    data.set_index('Random ID_index',inplace=True)
    
    #At this point the column number indeces have changed due to resetting the index
    #previous locator variables are no longer valid.
    
    
    
    '''REMOVAL DUMMY CODES - COMPLETELY MISSING PERFORMANCE DATA'''
    
    data['Removal - Completely missing performance data = 1'] = \
    Series((data['Item Count'] == 0),dtype=np.int32)
    
    
    
    '''REMOVAL DUMMY CODES - PARTIALLY MISSING PERFORMANCE DATA
    
    The lambda x function is used to pass
     variable "f" to the "apply" method which allows you
    to pass more complex functions in to elements of a DataFrame.
    '''
    
    f = lambda x: x in range(1,k)
    
    data['Removal - Partially missing performance data = 1'] = \
    Series(data['Item Count'].apply(f),dtype=np.int32) 
     
    
    '''NEXT IS TO CAPTURE RATER CONFIDENCE LEVELS, ALT REMOVAL REASONS'''
    
    #Find the column with rater confidence item
    
    #sub-select the valid sample as of this point in the logic for display
    #of confidence level value counts
    Rater_confidence_column_index = pd.Series(data.columns).str.contains("Based on")
    Rater_confidence_column = Rater_confidence_column_index[Rater_confidence_column_index == True].index[0]
        
    rata = data[(data["Removal - Completely missing performance data = 1"] == 0) \
    & (data["Removal - Partially missing performance data = 1"] == 0)]

    #show_raterconf_data(rata)
        
    '''RETRIEVE THE MINIMAL CONFIDENCE LEVEL'''
    
    Rating_given = "N"
    
    if Rating_given == "N":
        Rater_confidence_input = ["CD", "SD", "D"]
    else:
        Rater_confidence_input = ["CD", "SD", "D", "N"]
    
    g = lambda x: x in Rater_confidence_input 
         
     
    #this sends the master data file as a pandas dataframe to the function show_perf_data
    #for further processing 
    return show_jobs_data(request,data)



def show_jobs_data(request,data):
    context = dict()   
    
    #mostly formatting pandas objects so they look nice upon rendering in browser
    jobs_frame = data['Job Title'].value_counts().to_frame()
    jobs_frame.columns = ['Count of Unique Job Titles']
    context['jobs_pivot'] = jobs_frame.to_html()
    context['master_data'] = data   
    
    return render(request, 'twister/job_titles.html', context)


#user_start gives further instruction and then launches the file explorer
def user_start2(request):
    context = dict()
    version_now = "scicloud_pg_1.1"   
    conf_level_form = RaterConfForm()
    context['rater_conf_form'] = conf_level_form
    context['rata'] = rata.to_html()   
    return render(request, 'twister/user_start2.html', context)


def rater_conf(request):
    
    conf_level = request.POST['confidence_name']
    
    #return show_conf_data(request,data)
    return HttpResponse(conf_level)


def show_raterconf_data(request,data):
    context = dict()
    
    context['data_show'] = data.to_html()
    
    #mostly formatting pandas objects so they look nice upon rendering in browser
    jobs_frame = data['Job Title'].value_counts().to_frame()
    #jobs_frame['Job Title'] = jobs_frame.index
    #jobs_frame.index.names = ['Job Titles']
    jobs_frame.columns = ['Count of Unique Job Titles']
    
    context['jobs_pivot'] = jobs_frame.to_html()   
    
    #return HttpResponse("The sky grows dark...") ; this is its jsut a direct Response
    return render(request, 'twister/user_data.html', context)



#an examplar funcation for displaying operational data frame
def show_perf_data(request,data):
    context = dict()
    
    context['data_show'] = data.to_html()
    
    #mostly formatting pandas objects so they look nice upon rendering in browser
    jobs_frame = data['Job Title'].value_counts().to_frame()
    #jobs_frame['Job Title'] = jobs_frame.index
    #jobs_frame.index.names = ['Job Titles']
    jobs_frame.columns = ['Count of Unique Job Titles']
    
    context['jobs_pivot'] = jobs_frame.to_html()   
    
    #return HttpResponse("The sky grows dark...") ; this is its jsut a direct Response
    return render(request, 'twister/user_data.html', context)






#the eval export template
def export_empty_eval(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="/empty_eval.csv"'

    writer = csv.writer(response)
    
    header_row = ["Geo Level 1","Geo Level 2","Geo Level 3","Geo Level 4",\
    "Ratee First Name","Ratee Last Name","Ratee Unique ID","Last 4 SSN","Job Title",\
    "Email","Hire Date","Survey Group","Rater First Name","Rater Last Name","Rater Unique ID",\
    "Email","Duration","Ratee Status","metric1","metric2","metric3",\
    "Based on how often I observe this employee's behavior, I am confident in all of the ratings I just provided."]
 
    writer.writerow(header_row)
    
    return response


def full_docs(request):
     context = dict()
     z = "Full docs"
     context["print_y"] = z       
            
     return render(request, 'twister/full_docs.html', context)
    

