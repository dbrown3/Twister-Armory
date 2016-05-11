from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from django.template import loader, Context
from collections import  defaultdict
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
import json
import string
import StringIO
from datetime import datetime
import sys
import os
#import sklearn
#import pyttsx
#import time


#custom classes from twister
from TwisterDataUploader import TwisterDataUploader
#pandas work around related to an alert it sends
pd.set_option('mode.chained_assignment',None)

rata = pd.DataFrame()

# Twister's index is a data visualization of binary numbers swirling like a twister.
#the index template responds to mouse click to send user to user_start
'''
need pyttsx for this
def bang_speak(text_string):
    engine = pyttsx.init()
    engine.setProperty('volume', 1.00)
    engine.setProperty('rate', 150)
    engine.say(text_string)
    engine.runAndWait()
    return
'''

def index(request):
    context = dict() 
    #goodbye = "Thanks, that's all for me"   
    #bang_speak(goodbye)

    context ['first_name'] = " Phillip "
    context['last_name'] = " Gilmore "
    #return HttpResponse("The sky grows dark...") ; this is its jsut a direct Response
    return render(request, 'twister/index.html', context)



#user_start.html is the intro instructions, and offering performance data file selector
#to create_new_study, the file selector and submit button form link the submission action to create_new_study
#or to user_start2 "more info" link on the bottom of the html links user to full_docs.html 
def user_start(request):
    context = dict()
    start_time = str(datetime.now().time())    
    
    
    version_now = "'i don't want to leave no mysteries - Dave Chappelle'"   
    context["version_now"] = version_now
    
    data_entry_form = DataEntryForm()
    context['data_entry_form'] = data_entry_form
    context['start_time'] = start_time
        
    return render(request, 'twister/user_start.html', context)



#choose the file
def create_new_study(request):
    #assert False
    context = dict()
    start_time = request.POST.get('start_time')
    csv_file = request.FILES['csv_file']
    
    twister_data_uploader = TwisterDataUploader()
    
    with open(twister_data_uploader.file_system.location + "/" + csv_file.name, 'wb+') as destination:
        for chunk in csv_file.chunks():
            destination.write(chunk)

    twister_data_uploader.read_csv_data_from_file(csv_file)
    #print twister_data_uploader.column_headers
    
    na_codes = ['NULL','-99', 'N/A', 'n/a' '#N/A', 'blank','insufficient tenure']
    
    data = pd.read_csv(twister_data_uploader.file_system.location + "/" + csv_file.name,\
                               index_col=['Ratee Unique ID', 'Rater Unique ID'], \
                               na_values=na_codes)   
    
    '''FIRST WE GET AS FAR AS WE CAN WITH DATA MANIPULATION'''
    '''DEDUCE THE NUMBER OF ITEMS FOR MANY IMPORTANT OPERATIONS'''
    #k = int(raw_input("\nHow many items are in the scale? \n\
    #(do not count the final confidence item): "))
    
    #above snippet was originally used to request user input
    #given standard format, the metric columns should be deduced with the following
    in_name = str(csv_file.name)
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
        
    #this sends the master data file as a pandas dataframe to the function show_perf_data
    #for further processing 
    
    #mostly formatting pandas objects so they look nice upon rendering in browser
    jobs_frame = data['Job Title'].value_counts().to_frame()
    jobs_frame.columns = ['Count of Unique Job Titles']
    context['jobs_pivot'] = jobs_frame.to_html()
    
    context['col_headers'] = headerpacker(data) #takes a dataframe and returns an ordered json string of column headers
    context['master_data'] = data.to_json()
    context['in_name'] = in_name
    context['start_time'] = start_time
    #context['na_codes'] = na_codes
    context['k'] = k
         
    return render(request, 'twister/create_new_study.html', context)



#user_start gives further instruction and then launches the file explorer
def user_start2(request):
    #assert False
    context = dict()
    start_time = request.POST.get('start_time')
    #master data was passed from 'create_new_study', this is where Twister
    #would begin with rater confidence analyses
    
    k = int(request.POST.get('k'))    
    
    col_headers = pd.read_json(request.POST.get('col_headers'))
    col_headers.sort('order',inplace=True)
    col_headers = col_headers.header.tolist()

    data = pd.read_json(request.POST.get('master_data')) 
    data = data[col_headers]
               
    in_name = str(request.POST.get('in_name'))
    
    '''NEXT IS TO CAPTURE RATER CONFIDENCE LEVELS, ALT REMOVAL REASONS'''
    
    #Find the column with rater confidence item
    #sub-select the valid sample as of this point in the logic for display
    #of confidence level value counts
    Rater_confidence_column_index = pd.Series(data.columns).str.contains("Based on")
    Rater_confidence_column = Rater_confidence_column_index[Rater_confidence_column_index == True].index[0]
        
    rata = data[(data["Removal - Completely missing performance data = 1"] == 0) \
    & (data["Removal - Partially missing performance data = 1"] == 0)]

    #show_raterconf_data(rata)
        
    
    #mostly formatting pandas objects so they look nice upon rendering in browser
    conf_frame = rata.ix[:,Rater_confidence_column].value_counts().to_frame()
    conf_frame.columns = ['Cases Removed if Level Excluded']
    context['conf_pivot'] = conf_frame.to_html()
    context['col_headers'] = headerpacker(data)
    context['master_data'] = data.to_json()
    
    conf_level_form = RaterConfForm()
    context['rater_conf_form'] = conf_level_form
    context['rata'] = rata.to_html()
    context['in_name'] = in_name
    context['start_time'] = start_time
    context['k'] = k   
    
    #we'll send this to rater_conf in the form submission, which iis in the .html
    return render(request, 'twister/user_start2.html', context)


def rater_conf(request):
    
    context = dict()
    start_time = request.POST.get('start_time')
    
    '''RETRIEVE THE MINIMAL CONFIDENCE LEVEL'''
    k = int(request.POST.get('k'))
    conf_level = request.POST['confidence_name']
    in_name = str(request.POST.get('in_name'))
    col_headers = pd.read_json(request.POST.get('col_headers'))
    col_headers.sort('order',inplace=True)
    col_headers = col_headers.header.tolist()

    data = pd.read_json(request.POST.get('master_data')) 
    data = data[col_headers] 
    
    Rater_confidence_column_index = pd.Series(data.columns).str.contains("Based on")
    Rater_confidence_column = Rater_confidence_column_index[Rater_confidence_column_index == True].index[0]

     #picks up from classic twister
    Rating_given = conf_level
    
    if Rating_given == "N":
        Rater_confidence_input = ["CD", "SD", "D"]
    else:
        Rater_confidence_input = ["CD", "SD", "D", "N"]
    
    g = lambda x: x in Rater_confidence_input   
        
    '''REMOVAL DUMMY CODES - LACK OF RATER CONFIDENCE'''
    data['Removal - Lack of Rater Confidence = 1'] = Series(data.ix[:,Rater_confidence_column].apply(g), dtype = np.int32)
    context['col_headers'] = headerpacker(data)
    context['master_data'] = data.to_json()    
    context['in_name'] = in_name
    context['start_time'] = start_time
    context['k'] = k
    
    return render(request, 'twister/rater_conf.html', context)


def tenure_ask(request):
    #assert False
    context = dict()
    start_time = request.POST.get('start_time')
    
    collection_date = request.POST['date_field']
    k = int(request.POST.get('k'))
    in_name = str(request.POST.get('in_name'))
    
    col_headers = pd.read_json(request.POST.get('col_headers'))
    col_headers.sort('order',inplace=True)
    col_headers = col_headers.header.tolist()

    data = pd.read_json(request.POST.get('master_data')) 
    data = data[col_headers]   
       
    #coverts user inputted collection_date into datetime for later use in tenure calc
    removal_date = datetime.strptime(collection_date,"%m/%d/%Y")
    tenure_label = "Tenure (from Evaluation Hire Date to {})".format(collection_date)
    
    #needed below to convert the tenure label to a generic datatype in day units.
    #converted from nanoseconds.
    ns_per_day = 8.64*10**13
    def convert_tenure_type(x):
        try:
            return int(x)/ns_per_day
        except:
            data[tenure_label] = "Missing hire date" 
            
            
    if data['Hire Date'].nunique() < 3:
        data[tenure_label] = "All met tenure"
        tenure_req = 0
        data['Removal - Missing tenure data = 1'] = 0
        tenure_rem_label = 'Removal - Insufficient tenure (less than {} days) = 1'.format("some")        
        data[tenure_rem_label] = 0
     
    else:
        data[tenure_label] = removal_date - pd.to_datetime(data['Hire Date'],format="%m/%d/%Y")
        data[tenure_label] = data[tenure_label].apply(convert_tenure_type)
    
    #new temp label that isn't defined until the next view
    tenure_rem_label = 'Removal - Insufficient tenure (less than {} days) = 1'.format("some")
    
    hata = data[(data["Removal - Completely missing performance data = 1"] == 0) \
    & (data["Removal - Partially missing performance data = 1"] == 0) \
    & (data["Removal - Lack of Rater Confidence = 1"] == 0)]
    
    #sub-select the data relevant to each cutoff logic
    hatanalysis_0d = hata[['Item Avg',tenure_label]]
    hatanalysis_30d = hata[(hata[tenure_label] > 29)].ix[:,['Item Avg',tenure_label]]
    hatanalysis_60d = hata[(hata[tenure_label] > 59)].ix[:,['Item Avg',tenure_label]]
    hatanalysis_90d = hata[(hata[tenure_label] > 89)].ix[:,['Item Avg',tenure_label]]
    hatanalysis_180d = hata[(hata[tenure_label] > 179)].ix[:,['Item Avg',tenure_label]]
    hatanalysis_270d = hata[(hata[tenure_label] > 269)].ix[:,['Item Avg',tenure_label]]
    hatanalysis_365d = hata[(hata[tenure_label] > 364)].ix[:,['Item Avg',tenure_label]]
    
    #build a dataframe for displaying the cutoff logic and associated correlations
    df_tenure_report = DataFrame([\
    [(len(hata)-len(hatanalysis_30d)),\
    ("%.2f" % hatanalysis_30d.ix[:,0:2].corr().ix[0,1])],\
    [(len(hata)-len(hatanalysis_60d)),\
    ("%.2f" % hatanalysis_60d.ix[:,0:2].corr().ix[0,1])],\
    [(len(hata)-len(hatanalysis_90d)),\
    ("%.2f" % hatanalysis_90d.ix[:,0:2].corr().ix[0,1])],\
    [(len(hata)-len(hatanalysis_180d)),\
    ("%.2f" % hatanalysis_180d.ix[:,0:2].corr().ix[0,1])],\
    [(len(hata)-len(hatanalysis_270d)),\
    ("%.2f" % hatanalysis_270d.ix[:,0:2].corr().ix[0,1])],\
    [(len(hata)-len(hatanalysis_365d)),\
    ("%.2f" % hatanalysis_365d.ix[:,0:2].corr().ix[0,1])]],\
    index = [30,60,90,180,270,365],\
    columns=['Cases Excluded','r_(perf,tenure)'])
    
    df_tenure_report.index.name = 'Tenure cut (days)'
    
    del hatanalysis_30d,hatanalysis_60d,hatanalysis_90d,hatanalysis_180d,hatanalysis_270d,hatanalysis_365d 
    
    context['tenure_plot_tenure'] = hatanalysis_0d[tenure_label].tolist()
    context['tenure_plot_perf'] = hatanalysis_0d['Item Avg'].tolist()    
    context['df_tenure_report'] = df_tenure_report.to_html()
    context['30_Cases_Excluded'] = df_tenure_report.ix[30,'Cases Excluded']
    context['30_r_perf_tenure'] = df_tenure_report.ix[30,'r_(perf,tenure)']
    context['col_headers'] = headerpacker(data)
    context['master_data'] = data.to_json()
    context['tenure_label'] = tenure_label
    context['tenure_rem_label'] = tenure_rem_label
    context['in_name'] = in_name
    context['start_time'] = start_time
    context['k'] = k    
      
    #we'll send this to rater_conf in the form submission, which iis in the .html
    return render(request, 'twister/tenure_ask.html', context)



def show_and_match(request):
    #assert False
    context = dict()
    start_time = request.POST.get('start_time')
    
    tenure_req = int(request.POST['tenure_req'])
    k = int(request.POST['k'])
    tenure_label = str(request.POST['tenure_label'])
    tenure_rem_label = str(request.POST['tenure_rem_label'])
    in_name = str(request.POST.get('in_name'))
    
    col_headers = pd.read_json(request.POST.get('col_headers'))
    col_headers.sort('order',inplace=True)
    col_headers = col_headers.header.tolist()

    data = pd.read_json(request.POST.get('master_data')) 
    data = data[col_headers]  
    
    #build show_and_match.html with histo and exports SpinMaster
    '''REMOVAL DUMMY CODES - TENURE'''
    
    data['Removal - Missing tenure data = 1'] = \
    Series(data[tenure_label].isnull(),dtype=np.int32)
      
    
    tenure_rem_label = \
    'Removal - Insufficient tenure (less than {} days) = 1'.format(tenure_req)
    
    t = lambda x: x < tenure_req
    
    if data['Removal - Missing tenure data = 1'].all() == 1:
        data[tenure_rem_label] = 0
    else:
        data[tenure_rem_label] = Series(data[tenure_label].apply(t),dtype=np.int32)

   
    headers_perf_removals = ['Removal - Missing tenure data = 1',\
    tenure_rem_label, 'Removal - Completely missing performance data = 1',\
    'Removal - Partially missing performance data = 1', 'Removal - Lack of Rater Confidence = 1']

    
    zata = data[(data[headers_perf_removals].sum(axis=1)==0)]
    zata_mean = zata['Item Avg'].mean()
    zata_sd = zata['Item Avg'].std()
    
    zata.loc[:,'Z_Item Avg'] = \
        (zata['Item Avg'] - zata_mean)/zata_sd    


    '''PREPARING DATAFRAMES FOR OUTPUT TO XCEL TABS'''
    
    headers_list = []
    for i in range(len(data.columns)):
        headers_list = headers_list + [str(data.columns[i])]
    
    #First Name = headers_list[6]
    #Last = 7
    #SSN = 8
    #email = 10
    #Random ID = headers_list[-7] #
    out_headers = headers_list[6:9]
    out_headers.append(headers_list[10])
    out_headers.append(headers_list[-7])
    
    for i in range(0,7):
        out_headers.append(headers_list[i])
    
    for i in range(11,len(headers_list)-7):
        out_headers.append(headers_list[i])
    
    for i in range(len(headers_list)-5,len(headers_list)):
        out_headers.append(headers_list[i])
    
    #MASTER TAB
    #the below structure is simply formatting
    #to re-order the columns for the spin_master
    spin_master = data[out_headers[0:2]]
    spin_master = spin_master.join(data[out_headers[3]],how='outer')
    spin_master = spin_master.join(data[out_headers[2]],how='outer')
    spin_master = spin_master.join(data[out_headers[4]],how='outer')
    
    spin_master = pd.merge(spin_master,data.ix[:,0:6],how='outer',right_index =True, left_index=True)
    spin_master = spin_master.join(data['Job Title'],how='outer')
    
    #fix this so that bogus columns following the items don't end up overwriting your item statistics
    #you need to seek for the column location of 'Item Avg' and use this rather than +1+6
    
    item_avg_loc = data.columns.get_loc('Item Avg')
    
    spin_master = pd.merge(spin_master,data.ix[:,11:(item_avg_loc+6)],\
    how='outer',right_index =True, left_index=True)
    spin_master = pd.merge(spin_master,data.ix[:,-6:],\
    how='outer',right_index =True, left_index=True)
    
    #the out_headers have problem matching dataframe columns headers 
    #when you get to the items; probably due to special character decoding
    #this is why the excessive merging just to re-order columns;
    #if i could pass the out_headers list, this would be more elegant 
    
    #creating a df that can be analyzed on performance-side
    data_spin_temp = data
    data_spin_temp['Sum Dummies'] = data_spin_temp[headers_perf_removals].sum(axis=1)
    data_spinalysis = data_spin_temp[data_spin_temp['Sum Dummies']==0]
    
    data_spinalysis = data_spinalysis.drop('Sum Dummies',1)
    
    #final_removal_headers = ['Removal - Not Matched = 1'] + master_tab_dummyheaders
    #data11['Final Sample Code'] = data11.ix[:,final_removal_headers].sum(axis= 1)
    #Final_Data = data11[data11['Final Sample Code']==0]
    #Final_Data = Final_Data.drop('Final Sample Code', 1)   
    
    #SUMMARY TAB
    summary = data.describe() 
     
    #are these indeces right?
    data_spinalysis.ix[:,18:(18+k)].columns
    corrs_items = data_spinalysis.ix[:,18:(18+k)].corr()
      
    #SOURCE TABS
    df_final_titles = data_spinalysis['Job Title'].value_counts()
    df_final_raters = data_spinalysis['Rater Unique ID'].value_counts()
    df_final_geo1 = data_spinalysis['Geo Level 1'].value_counts()
    df_final_geo2 = data_spinalysis['Geo Level 2'].value_counts()
    df_final_geo3 = data_spinalysis['Geo Level 3'].value_counts()
    df_final_geo4 = data_spinalysis['Geo Level 4'].value_counts()
       
    #Floats indicating ratio of observations to error sources
    #useful in logic related to the appropriateness of ANOVA
    #Note that these are all based on the cleaned sample 'data_spinalysis'
    subselect = data_spinalysis[['Item Avg', 'Job Title', 'Rater Unique ID',\
    'Geo Level 1', 'Geo Level 2', 'Geo Level 3', 'Geo Level 4']]
       
    
    '''FOR JOB TITLES'''
    
    try:
        ratio_titles = float(len(data_spinalysis) / len(df_final_titles))
        if len(df_final_titles) > 1:
            arrDict = {}        
            #arrList = [[] for i in range(0,len(df_final_titles))]        
            for i in range(0,len(df_final_titles)):
                arrDict[i] = subselect[subselect['Job Title'] == \
                str(df_final_titles.index.values[i])]['Item Avg'].values
            
            #using the asterisk then method somehow allows the values to pass
            #Larry has seen this concept in the world of C++ programming
            f_titles, p_titles =  stats.f_oneway(*arrDict.values())
            crit_p_titles = 0.05/(len(df_final_titles)-1)
            
            '''JOB TITLES CONCLUSIONS'''
            if p_titles < crit_p_titles and ratio_titles > 10 :
                conclusion_titles = 'Significant difference here. Dig in deeper.'
            elif p_titles < crit_p_titles:
                conclusion_titles = 'There might be a difference, but confidence is low.'
            elif p_titles > crit_p_titles and ratio_titles > 10 :
                conclusion_titles = 'Evidence indicates no significant difference.'
            else:
                conclusion_titles = 'Little confidence in this, but no apparent differences observed.'
            
        else:
            f_titles, p_titles, crit_p_titles, conclusion_titles = (float(),float(),float(),'')
    
        
    except:
        ratio_titles = "Empty titles"
        f_titles, p_titles, crit_p_titles, conclusion_titles = (float(),float(),float(),'')
           
    '''FOR RATERS'''
    
    try:
        ratio_raters = float(len(data_spinalysis) / len(df_final_raters))
        if len(df_final_raters) > 1:
            arrDict = {}        
            #arrList = [[] for i in range.(0,len(df_final_titles))]        
            for i in range(0,len(df_final_raters)):
                try:
                    arrDict[i] = subselect[subselect['Rater Unique ID'] == \
                    str(df_final_raters.index.values[i])]['Item Avg'].values
                except:
                    arrDict[i] = subselect[subselect['Rater Unique ID'] == \
                    df_final_raters.index.values[i]]['Item Avg'].values
            
            #using the asterisk then method somehow allows the values to pass
            #Larry has seen this concept in the world of C++ programming
            f_raters, p_raters =  stats.f_oneway(*arrDict.values())
            crit_p_raters = 0.05/(len(df_final_raters)-1)
            
            '''RATERS CONCLUSIONS'''
            if p_raters < crit_p_raters and ratio_raters > 10 :
                conclusion_raters = 'Significant difference here. Dig in deeper.'
            elif p_raters < crit_p_raters:
                conclusion_raters = 'There might be a difference, but confidence is low.'
            elif p_raters > crit_p_raters and ratio_raters > 10 :
                conclusion_raters = 'Evidence indicates no significant difference.'
            else:
                conclusion_raters = 'Little confidence in this, but no apparent differences observed.'
            
        else:
            f_raters, p_raters, crit_p_raters, conclusion_raters = (float(),float(),float(),'')
        
    except:
        ratio_raters = "Empty raters"
        f_raters, p_raters, crit_p_raters, conclusion_raters = (float(),float(),float(),'')
    
   
    '''FOR GEO 1'''
    
    try:
        ratio_final_geo1 = float(len(data_spinalysis) / len(df_final_geo1))
        if len(df_final_geo1) > 1:
            arrDict = {}        
            #arrList = [[] for i in range(0,len(df_final_titles))]        
            for i in range(0,len(df_final_geo1)):
                try:
                    arrDict[i] = subselect[subselect['Geo Level 1'] == \
                    str(df_final_geo1.index.values[i])]['Item Avg'].values
                except:
                    arrDict[i] = subselect[subselect['Geo Level 1'] == \
                    df_final_geo1.index.values[i]]['Item Avg'].values
                       
            
            #using the asterisk then method somehow allows the values to pass
            #Larry has seen this concept in the world of C++ programming
            f_geo1, p_geo1 =  stats.f_oneway(*arrDict.values())
            crit_p_geo1 = 0.05/(len(df_final_geo1)-1)
            
            '''GEO1 CONCLUSIONS'''
            if p_geo1 < crit_p_geo1 and ratio_final_geo1 > 10 :
                conclusion_geo1 = 'Significant difference here. Dig in deeper.'
            elif p_geo1 < crit_p_geo1:
                conclusion_geo1 = 'There might be a difference, but confidence is low.'
            elif p_geo1 > crit_p_geo1 and ratio_final_geo1 > 10 :
                conclusion_geo1 = 'Evidence indicates no significant difference.'
            else:
                conclusion_geo1 = 'Little confidence in this, but no apparent differences observed.'
            
        else:
            f_geo1, p_geo1, crit_p_geo1, conclusion_geo1 = (float(),float(),float(),'')
        
    except:
        ratio_final_geo1 = "Empty geo1"
        f_geo1, p_geo1, crit_p_geo1, conclusion_geo1 = (float(),float(),float(),'')
        
    '''FOR GEO 2'''
    
    try:
        ratio_final_geo2 = float(len(data_spinalysis) / len(df_final_geo2))
        if len(df_final_geo2) > 1:
            arrDict = {}        
            #arrList = [[] for i in range(0,len(df_final_titles))]        
            for i in range(0,len(df_final_geo2)):
                try:
                    arrDict[i] = subselect[subselect['Geo Level 2'] == \
                    str(df_final_geo2.index.values[i])]['Item Avg'].values
                except:
                    arrDict[i] = subselect[subselect['Geo Level 2'] == \
                    df_final_geo2.index.values[i]]['Item Avg'].values
    
            #using the asterisk then method somehow allows the values to pass
            #Larry has seen this concept in the world of C++ programming
            f_geo2, p_geo2 =  stats.f_oneway(*arrDict.values())
            crit_p_geo2 = 0.05/(len(df_final_geo2)-1)
            
            '''GEO2 CONCLUSIONS'''
            if p_geo2 < crit_p_geo2 and ratio_final_geo2 > 10 :
                conclusion_geo2 = 'Significant difference here. Dig in deeper.'
            elif p_geo2 < crit_p_geo2:
                conclusion_geo2 = 'There might be a difference, but confidence is low.'
            elif p_geo2 > crit_p_geo2 and ratio_final_geo2 > 10 :
                conclusion_geo2 = 'Evidence indicates no significant difference.'
            else:
                conclusion_geo2 = 'Little confidence in this, but no apparent differences observed.'
            
        else:
            f_geo2, p_geo2, crit_p_geo2, conclusion_geo2 = (float(),float(),float(),'')
        
    except:
        ratio_final_geo2 = "Empty geo2"
        f_geo2, p_geo2, crit_p_geo2, conclusion_geo2 = (float(),float(),float(),'') 
    
    '''GEO LEVEL 3'''
    
    try:
        ratio_final_geo3 = float(len(data_spinalysis) / len(df_final_geo3))
        if len(df_final_geo3) > 1:
            arrDict = {}        
            #arrList = [[] for i in range(0,len(df_final_titles))]        
            for i in range(0,len(df_final_geo3)):
                try:
                    arrDict[i] = subselect[subselect['Geo Level 3'] == \
                    str(df_final_geo3.index.values[i])]['Item Avg'].values
                except:
                    arrDict[i] = subselect[subselect['Geo Level 3'] == \
                    df_final_geo3.index.values[i]]['Item Avg'].values
    
            #using the asterisk then method somehow allows the values to pass
            #Larry has seen this concept in the world of C++ programming
            f_geo3, p_geo3 =  stats.f_oneway(*arrDict.values())
            crit_p_geo3 = 0.05/(len(df_final_geo3)-1)
            
            '''GEO3 CONCLUSIONS'''
            if p_geo3 < crit_p_geo3 and ratio_final_geo3 > 10 :
                conclusion_geo3 = 'Significant difference here. Dig in deeper.'
            elif p_geo3 < crit_p_geo3:
                conclusion_geo3 = 'There might be a difference, but confidence is low.'
            elif p_geo3 > crit_p_geo3 and ratio_final_geo3 > 10 :
                conclusion_geo3 = 'Evidence indicates no significant difference.'
            else:
                conclusion_geo3 = 'Little confidence in this, but no apparent differences observed.'
            
        else:
            f_geo3, p_geo3, crit_p_geo3, conclusion_geo3 = (float(),float(),float(),'')  
    except:
        ratio_final_geo3 = "Empty geo3"
        f_geo3, p_geo3, crit_p_geo3, conclusion_geo3 = (float(),float(),float(),'')
    
    '''GEO LEVEL 4'''
    
    try:
        ratio_final_geo4 = float(len(data_spinalysis) / len(df_final_geo4))
        if len(df_final_geo4) > 1:
            arrDict = {}        
            #arrList = [[] for i in range(0,len(df_final_titles))]        
            for i in range(0,len(df_final_geo4)):
                try:
                    arrDict[i] = subselect[subselect['Geo Level 4'] == \
                    str(df_final_geo4.index.values[i])]['Item Avg'].values
                except:
                    arrDict[i] = subselect[subselect['Geo Level 4'] == \
                    df_final_geo4.index.values[i]]['Item Avg'].values
    
            #using the asterisk then method somehow allows the values to pass
            #Larry has seen this concept in the world of C++ programming
            f_geo4, p_geo4 =  stats.f_oneway(*arrDict.values())
            crit_p_geo4 = 0.05/(len(df_final_geo4)-1)
            
            '''GEO4 CONCLUSIONS'''
            if p_geo4 < crit_p_geo4 and ratio_final_geo4 > 10 :
                conclusion_geo4 = 'Significant difference here. Dig in deeper.'
            elif p_geo4 < crit_p_geo4:
                conclusion_geo4 = 'There might be a difference, but confidence is low.'
            elif p_geo4 > crit_p_geo4 and ratio_final_geo4 > 10 :
                conclusion_geo4 = 'Evidence indicates no significant difference.'
            else:
                conclusion_geo4 = 'Little confidence in this, but no apparent differences observed.'
            
        else:
            f_geo4, p_geo4, crit_p_geo4, conclusion_geo4 = (float(),float(),float(),'')
        
    except:
        ratio_final_geo4 = "Empty geo4"
        f_geo4, p_geo4, crit_p_geo4, conclusion_geo4 = (float(),float(),float(),'')      
    
    #REPORTS TAB
        
    #Computation of standardized Cronbach's alphs (scale reliability)
    #requires k = number of items, and r_bar_lower which is the 
    #average of all unique split-half correlations between items
    #I compute this from the return of the corr function, which is full matrix
    
    sum_corrs = corrs_items.sum().sum()
    r_bar_lower = (sum_corrs-k) / (k*(k-1))
      
    full_alpha_standard = k*r_bar_lower / (1+(k-1)*r_bar_lower)
    item_summary = compute_cronbachs(k,data_spinalysis)      
       
    df_report = DataFrame([['Scale Items', k], ['Sample size',len(data_spinalysis)],\
    ['r-bar', ("%.2f" % r_bar_lower)],\
    ['alpha_standard', ("%.2f" % full_alpha_standard)],\
    ['COVARIATES','(Ratio values over 10 \n can be analyzed with confidence)'], \
    ['Job titles','ratio = {}'.format(ratio_titles), \
    ("%.4f" % f_titles), ("%.4f" % p_titles), ("%.4f" % crit_p_titles), conclusion_titles], \
    ['Raters','ratio = {}'.format(ratio_raters), \
    ("%.4f" % f_raters), ("%.4f" % p_raters), ("%.4f" % crit_p_raters), conclusion_raters], \
    ['Geo Level 1','ratio = {}'.format(ratio_final_geo1), \
    ("%.4f" % f_geo1), ("%.4f" % p_geo1), ("%.4f" % crit_p_geo1), conclusion_geo1], \
    ['Geo Level 2','ratio = {}'.format(ratio_final_geo2), \
    ("%.4f" % f_geo2), ("%.4f" % p_geo2), ("%.4f" % crit_p_geo2), conclusion_geo2], \
    ['Geo Level 3','ratio = {}'.format(ratio_final_geo3), \
    ("%.4f" % f_geo3), ("%.4f" % p_geo3), ("%.4f" % crit_p_geo3), conclusion_geo3], \
    ['Geo Level 4','ratio = {}'.format(ratio_final_geo4), \
    ("%.4f" % f_geo4), ("%.4f" % p_geo4), ("%.4f" % crit_p_geo4), conclusion_geo4]], \
    columns=['Label','Values','ANOVA F_test', 'p_value', 'p_cutoff', 'Spinsight(c)'])
    
    '''
    Printed out to a csv format. File name adjusted manually. NA values
    specified otherwise will be whitespace
    '''
    
    outfile = "Spin_Results"    
    #in_name was parsed when Tkinter first brings in the data files common name
    outfilename = outfile+"("+in_name+")"
      
    #custom tab labels
    item_summary_tab = "Item Summary (k = {})".format(k)
    corrs_items_tab = "Correls Items (n = {})".format(len(data_spinalysis))
    titles_tab = "Job Titles (uniq = {})".format(len(df_final_titles))
    raters_tab = "Raters (uniq = {})".format(len(df_final_raters))
    geo1_tab = "Geo 1 (uniq = {})".format(len(df_final_geo1))
    geo2_tab = "Geo 2 (uniq = {})".format(len(df_final_geo2))
    geo3_tab = "Geo 3 (uniq = {})".format(len(df_final_geo3))
    geo4_tab = "Geo 4 (uniq = {})".format(len(df_final_geo4))
   
   
    match_frame_headers = ['Ratee First Name','Ratee Last Name','Email','Last 4 SSN','Random ID','Ratee Unique ID']
    match_frame = spin_master[match_frame_headers]
    
    scale_summary = df_report.ix[0:3,['Label','Values']]
    covariate_summary = df_report.ix[5:,:]
    
    short_heads = shorten_labels(corrs_items.index.values)    
    corrs_items.index = short_heads
    
       
    '''VISUALIZING PERFORMANCE VARIABLE'''
           
    #zata is a df assuming 'Z_Item Avg' is standardized perf column
    context['twisted_metric'] = zata['Z_Item Avg'].tolist()           
    context['col_headers'] = headerpacker(spin_master)
    context['master_data'] = spin_master.to_json() #spin_master is the new master data which will later merge with match
    context['covariate_summary'] = covariate_summary.to_html(float_format=lambda x: '%.4f' % x,index=False,na_rep='')
    context['match_frame'] = match_frame.to_html(index=False,na_rep='')
    context['scale_summary'] = scale_summary.to_html(header=False,index=False,na_rep='')
    context['item_summary'] = item_summary.to_html(float_format=lambda x: '%.2f' % x,na_rep='')
    context['corrs_items'] = corrs_items.to_html(float_format=lambda x: '%.2f' % x,na_rep='')
    context['tenure_label'] = tenure_label
    context['tenure_rem_label'] = tenure_rem_label
    context['in_name'] = in_name
    context['start_time'] = start_time
    context['k'] = k   
               
    #we'll send this to show_and_match in the form submission, which is in the .html
    return render(request, 'twister/show_and_match.html', context)



def match_and_merge(request):
    context = dict()
    start_time = request.POST.get('start_time')
    
    
    #Keep what you need moving forward. Derek's Twister is fairly self-contained, but needs
    # spin_master which is merged with the newly csv_read data_match dataframe taken from this dataentry form
    #in views.merge_and_master
    #I don't convert these out of their json form because i'm just passing them to the next view
    context['col_headers'] = request.POST.get('col_headers')   
    context['master_data'] = request.POST.get('master_data') 
    context['start_time'] = start_time
    context['in_name'] = str(request.POST.get('in_name'))
    context['tenure_label'] = str(request.POST.get('tenure_label'))
    context['tenure_rem_label'] = str(request.POST['tenure_rem_label'])
        
    #these two will be used to capture the .csv file        
    data_entry_form = DataEntryForm()
    context['data_entry_form'] = data_entry_form
    
    
            
    return render(request, 'twister/match_and_merge.html', context)



def merge_and_master(request):
    context = dict()
    
    end_time = str(datetime.now().time())
    
    start_time = request.POST.get('start_time')
    
    in_name = str(request.POST.get('in_name'))
    tenure_label = str(request.POST.get('tenure_label'))
    tenure_rem_label = str(request.POST['tenure_rem_label'])

    
    col_headers = pd.read_json(request.POST.get('col_headers'))
    col_headers.sort('order',inplace=True)
    col_headers = col_headers.header.tolist()

    spin_master = pd.read_json(request.POST.get('master_data')) 
    spin_master = spin_master[col_headers]    
    
    csv_file = request.FILES['csv_file']

    twister_data_uploader = TwisterDataUploader()
    
    with open(twister_data_uploader.file_system.location + "/" + csv_file.name, 'wb+') as destination:
        for chunk in csv_file.chunks():
            destination.write(chunk)
    
    twister_data_uploader.read_csv_data_from_file(csv_file)
    #print twister_data_uploader.column_headers
    
    data_match = pd.read_csv(twister_data_uploader.file_system.location + "/" + csv_file.name,\
                             na_values=['NULL'], encoding = 'utf-8')   
    
    data_match['Random ID as Index'] = data_match['Random ID']
    data_match = data_match.set_index('Random ID as Index')
    
    #Create Quality Control(QC) by first reformatting 3 of the QC metrics into float types
    
    data_match['FALSIFICATION'] = data_match['FALSIFICATION'].replace('%','',regex=True).astype('float')/100
    data_match['CONSISTENCY'] = data_match['CONSISTENCY'].replace('%','',regex=True).astype('float')/100
    data_match['CLICK_THROUGH'] = data_match['CLICK_THROUGH'].replace('%','',regex=True).astype('float')/100
    
    #Let's Rename Email to Match Email so that it is unique
    #data_match['Email'] = data_match['Match Email']
    data_match =  data_match.rename(columns={'EMAIL': 'Match Email'})
    
    Ptim_Dummy = lambda x: x != 0 and x <=11.12
    Pim_Dummy = lambda x: x <= 12.97
    Falsification_Dummy = lambda x: x >= 0.75
    Con_Dummy = lambda x: x <= 0.67
    Clik_Dummy = lambda x: x >= 0.6641
    Seq_Dummy = lambda x: x >= 2
    Lcs_Dummy = lambda x: x >= 17
    Quality_column = lambda x: x != 0 
    
    #Apply the Lambdas that were created
    data_match['QC Ptim'] = Series(data_match['PPI_TOTAL_ITEM_MINUTES'].apply(Ptim_Dummy),dtype=np.int32)
    data_match['QC Pim'] = Series(data_match['PPI_MINUTES'].apply(Pim_Dummy),dtype=np.int32)
    data_match['QC Falsification'] = Series(data_match['FALSIFICATION'].apply(Falsification_Dummy),dtype=np.int32)
    data_match['QC Con'] = Series(data_match['CONSISTENCY'].apply(Con_Dummy),dtype=np.int32)
    data_match['QC Clik'] = Series(data_match['CLICK_THROUGH'].apply(Clik_Dummy),dtype=np.int32)
    data_match['QC Seq'] = Series(data_match['SEQUENCE'].apply(Seq_Dummy),dtype=np.int32)
    data_match['QC Lcs'] = Series(data_match['LCS_LENGTH'].apply(Lcs_Dummy),dtype=np.int32)
    
    Quality_control_Dummy_headers = ['QC Ptim', 'QC Pim', 'QC Falsification', 'QC Con', 'QC Clik', 'QC Seq', 'QC Lcs']
    Quality_control_headers = ['PPI_TOTAL_ITEM_MINUTES', 'PPI_MINUTES', 'FALSIFICATION', 'CONSISTENCY', 'CLICK_THROUGH', 'SEQUENCE', 'LCS_LENGTH']
    data_match['Removal - Quality Control = 1'] = Series(data_match.ix[:,Quality_control_Dummy_headers].sum(axis = 1).apply(Quality_column),dtype=np.int32)
    
    #Create new data frame excluding Quality Control removals
    Clean_data_match = data_match[data_match['Removal - Quality Control = 1']  != 1]
    
    #Determine mean and std of each dimension
    
    Headers_PPI2 = ['ACCEPTANCE_OF_AUTHORITY', 'AMBITION', 'ANALYTICAL', 'ASSERTIVENESS',\
     'ATTENTION_TO_DETAILS', 'BUSINESS_ATTITUDE', 'CHANGE_ORIENTATION', \
     'COMPETITIVE_FIERCENESS', 'CONFIDENCE', 'CONSCIENTIOUSNESS', 'COOPERATIVENESS', \
     'CREATIVITY', 'DISCIPLINE', 'EMOTIONAL_CONSISTENCY', 'ENERGY', 'FLEXIBILITY', \
     'INSIGHT_INTO_OTHERS', 'JOB_ATMOSPHERE', 'LEADERSHIP_IMPACT', 'MENTAL_FLEXIBILITY', \
     'NEED_FOR_RECOGNITION', 'NUMERICAL_REASONING', 'OBJECTIVITY', 'OPTIMISM', \
     'ORGANIZATIONAL_STRUCTURE', 'ORGANIZATIONAL_TENDENCY', 'PACE', 'PEOPLE_ORIENTATION', \
     'PRACTICAL', 'REALISTIC_THINKING', 'REFLECTIVE', 'RISK_TAKER', 'SELF_RELIANCE', \
     'SOCIABILITY', 'SOCIAL_CONTACT', 'STRESS_TOLERANCE', 'TEAM_ORIENTATION', \
     'TOUGH_MINDEDNESS', 'VERBAL_REASONING']
    
    #Creating Z Scores for each dimension
    Dimension_descriptives1 = Clean_data_match.ix[:,Headers_PPI2].describe()
    Dimension_descriptives2 = Clean_data_match.ix[:,Headers_PPI2]
    #Dimension_Upper_Lower = Dimension_descriptives.ix[1:3,:]
    
    for col in Dimension_descriptives2:
        col_zscore = col + '_zscore'
        Dimension_descriptives2[col_zscore] = (Dimension_descriptives2[col] - Dimension_descriptives2[col].mean())/Dimension_descriptives2[col].std(ddof=0)
    
    '''Population parameters for PPI2+PMA are read in from 
    a prepared .csv file saved on a folder in my desktop. Only PPI2+PMA at this point.
    
    Below, the try statement reads in the .csv.
    In case this file is dislocated, the except statement uses the hardcoded values.
    I like the read_csv better because it gives an independent way to manage
    the parameter estimates. But the values Are essential to calculations, so 
    a backup hardcode may be necessary.
    '''
    
    
    #try:
    #    ppi2_pop_params = pd.read_csv('C:\Users\dbrown3\Desktop\PPI2_PMA_PopMeanStd.csv')
    #except:
    ppi2_pop_params_dict = {'Dimension Name': ['ACCEPTANCE_OF_AUTHORITY', 'AMBITION', 'ANALYTICAL', 'ASSERTIVENESS',\
     'ATTENTION_TO_DETAILS', 'BUSINESS_ATTITUDE', 'CHANGE_ORIENTATION', \
     'COMPETITIVE_FIERCENESS', 'CONFIDENCE', 'CONSCIENTIOUSNESS', 'COOPERATIVENESS', \
     'CREATIVITY', 'DISCIPLINE', 'EMOTIONAL_CONSISTENCY', 'ENERGY', 'FLEXIBILITY', \
     'INSIGHT_INTO_OTHERS', 'JOB_ATMOSPHERE', 'LEADERSHIP_IMPACT', 'MENTAL_FLEXIBILITY', \
     'NEED_FOR_RECOGNITION', 'NUMERICAL_REASONING', 'OBJECTIVITY', 'OPTIMISM', \
     'ORGANIZATIONAL_STRUCTURE', 'ORGANIZATIONAL_TENDENCY', 'PACE', 'PEOPLE_ORIENTATION', \
     'PRACTICAL', 'REALISTIC_THINKING', 'REFLECTIVE', 'RISK_TAKER', 'SELF_RELIANCE', \
     'SOCIABILITY', 'SOCIAL_CONTACT', 'STRESS_TOLERANCE', 'TEAM_ORIENTATION', \
     'TOUGH_MINDEDNESS', 'VERBAL_REASONING'],\
    'Mean.p': [63.96,54.13,53.8,55.15,60.02,58.44,48.96,51.1,51.09,61.39,57.06,53.46,\
    60.54,60.52,57.04,54.62,60.8,59.35,52.18,52.47,50.5,51.25,56.82,57.64,47.57,63.99,55.06,\
    62.33,60.12,45.89,52.86,52.02,43.68,61.53,53.47,54.77,53.84,48.59,53.69],\
    'Std.p': [18.83,16.87,12.33,13.47,15.6,15.84,13.26,13.82,11.92,16.06,14.3,16.66,\
    17.45,18.34,15.48,13,16.09,13.88,12.52,13.76,13.84,15.53,14.87,14.49,11.93,16.69,14.88,\
    14.55,14.05,12.86,12.79,14.28,12.39,15.51,13.26,13.21,12.36,13.12,15.09]}    
    
    ppi2_pop_params = pd.DataFrame(ppi2_pop_params_dict, columns=['Dimension Name',\
        'Mean.p','Std.p'])
    
    
    #The full version would need to filter out non-relevant assessments in order
    #for the standardization values to be accurate.
    
    #if matched_first starts with "Zzt", that is a test account
    
    #Because the length of the parameters dataframe is known a priori
    #(39 dimensions, each with a mean and std),
    #this list can be pre-written to loop through and standardize the values in 
    #my master file called 'data'
    
    for i in range(0,39):
        z_name = '_'.join(('z',ppi2_pop_params.ix[i,'Dimension Name']))
        Dimension_descriptives2[z_name] = (Dimension_descriptives2[ppi2_pop_params.ix[i,'Dimension Name']] \
    - ppi2_pop_params[ppi2_pop_params['Dimension Name']==ppi2_pop_params.ix[i,'Dimension Name']].ix[:,'Mean.p'].values)\
    / ppi2_pop_params[ppi2_pop_params['Dimension Name']==ppi2_pop_params.ix[i,'Dimension Name']].ix[:,'Std.p'].values
    
    
    Sample_Zscored_Headers_PPI2 = ['ACCEPTANCE_OF_AUTHORITY_zscore', 'AMBITION_zscore', \
    'ANALYTICAL_zscore', 'ASSERTIVENESS_zscore','ATTENTION_TO_DETAILS_zscore', \
    'BUSINESS_ATTITUDE_zscore', 'CHANGE_ORIENTATION_zscore', 'COMPETITIVE_FIERCENESS_zscore', \
    'CONFIDENCE_zscore', 'CONSCIENTIOUSNESS_zscore', 'COOPERATIVENESS_zscore', \
    'CREATIVITY_zscore', 'DISCIPLINE_zscore', 'EMOTIONAL_CONSISTENCY_zscore', 'ENERGY_zscore', \
    'FLEXIBILITY_zscore', 'INSIGHT_INTO_OTHERS_zscore', 'JOB_ATMOSPHERE_zscore', 'LEADERSHIP_IMPACT_zscore', \
    'MENTAL_FLEXIBILITY_zscore', 'NEED_FOR_RECOGNITION_zscore', 'NUMERICAL_REASONING_zscore', \
    'OBJECTIVITY_zscore', 'OPTIMISM_zscore', 'ORGANIZATIONAL_STRUCTURE_zscore', \
    'ORGANIZATIONAL_TENDENCY_zscore', 'PACE_zscore', 'PEOPLE_ORIENTATION_zscore', \
    'PRACTICAL_zscore', 'REALISTIC_THINKING_zscore', 'REFLECTIVE_zscore', 'RISK_TAKER_zscore', \
    'SELF_RELIANCE_zscore', 'SOCIABILITY_zscore', 'SOCIAL_CONTACT_zscore', 'STRESS_TOLERANCE_zscore', \
    'TEAM_ORIENTATION_zscore', 'TOUGH_MINDEDNESS_zscore', 'VERBAL_REASONING_zscore']
    
    
    Population_dummy_coded_Zscored_Headers_PPI2 = ['z_ACCEPTANCE_OF_AUTHORITY', 'z_AMBITION',\
    'z_ANALYTICAL', 'z_ASSERTIVENESS', 'z_ATTENTION_TO_DETAILS', 'z_BUSINESS_ATTITUDE', 'z_CHANGE_ORIENTATION','z_COMPETITIVE_FIERCENESS',\
    'z_CONFIDENCE', 'z_CONSCIENTIOUSNESS', 'z_COOPERATIVENESS', 'z_CREATIVITY', 'z_DISCIPLINE', \
     'z_EMOTIONAL_CONSISTENCY', 'z_ENERGY', 'z_FLEXIBILITY', 'z_INSIGHT_INTO_OTHERS', 'z_JOB_ATMOSPHERE', \
     'z_LEADERSHIP_IMPACT', 'z_MENTAL_FLEXIBILITY', 'z_NEED_FOR_RECOGNITION', 'z_NUMERICAL_REASONING', 'z_OBJECTIVITY', \
     'z_OPTIMISM', 'z_ORGANIZATIONAL_STRUCTURE', 'z_ORGANIZATIONAL_TENDENCY', 'z_PACE', 'z_PEOPLE_ORIENTATION', \
     'z_PRACTICAL', 'z_REALISTIC_THINKING', 'z_REFLECTIVE', 'z_RISK_TAKER', 'z_SELF_RELIANCE', 'z_SOCIABILITY', \
     'z_SOCIAL_CONTACT', 'z_STRESS_TOLERANCE', 'z_TEAM_ORIENTATION', 'z_TOUGH_MINDEDNESS', 'z_VERBAL_REASONING']
    
    #Trying to find a code creates dummy code column for assessment outliers after evaluating whether there are 5 or more assessment outliers across all dimensions for the people in this data frame who have passed quality control.
    Sample_Assessment_outlier_dummy_code_columns = Dimension_descriptives2.ix[:,Sample_Zscored_Headers_PPI2]
    Population_Assessment_outlier_dummy_code_columns = Dimension_descriptives2.ix[:,Population_dummy_coded_Zscored_Headers_PPI2]
    
    
    Assessment_Outlier_Column = lambda x: np.abs(x) > 3
    
    for cols in Sample_Assessment_outlier_dummy_code_columns:
        cols_dummies = cols + '_dummy'
        Sample_Assessment_outlier_dummy_code_columns[cols_dummies] = Series(Sample_Assessment_outlier_dummy_code_columns[cols].apply(Assessment_Outlier_Column),dtype=np.int32)
    
    for cols in Population_Assessment_outlier_dummy_code_columns:
        pop_cols_dummies = cols + '_dummy'
        Population_Assessment_outlier_dummy_code_columns[pop_cols_dummies] = Series(Population_Assessment_outlier_dummy_code_columns[cols].apply(Assessment_Outlier_Column),dtype=np.int32)
    
    Sample_Dummy_coded_Zscored_Headers_PPI2 = ['ACCEPTANCE_OF_AUTHORITY_zscore_dummy', 'AMBITION_zscore_dummy', \
    'ANALYTICAL_zscore_dummy', 'ASSERTIVENESS_zscore_dummy','ATTENTION_TO_DETAILS_zscore_dummy', \
    'BUSINESS_ATTITUDE_zscore_dummy', 'CHANGE_ORIENTATION_zscore_dummy', 'COMPETITIVE_FIERCENESS_zscore_dummy', \
    'CONFIDENCE_zscore_dummy', 'CONSCIENTIOUSNESS_zscore_dummy', 'COOPERATIVENESS_zscore_dummy', \
    'CREATIVITY_zscore_dummy', 'DISCIPLINE_zscore_dummy', 'EMOTIONAL_CONSISTENCY_zscore_dummy', 'ENERGY_zscore_dummy', \
    'FLEXIBILITY_zscore_dummy', 'INSIGHT_INTO_OTHERS_zscore_dummy', 'JOB_ATMOSPHERE_zscore_dummy', 'LEADERSHIP_IMPACT_zscore_dummy', \
    'MENTAL_FLEXIBILITY_zscore_dummy', 'NEED_FOR_RECOGNITION_zscore_dummy', 'NUMERICAL_REASONING_zscore_dummy', \
    'OBJECTIVITY_zscore_dummy', 'OPTIMISM_zscore_dummy', 'ORGANIZATIONAL_STRUCTURE_zscore_dummy', \
    'ORGANIZATIONAL_TENDENCY_zscore_dummy', 'PACE_zscore_dummy', 'PEOPLE_ORIENTATION_zscore_dummy', \
    'PRACTICAL_zscore_dummy', 'REALISTIC_THINKING_zscore_dummy', 'REFLECTIVE_zscore_dummy', 'RISK_TAKER_zscore_dummy', \
    'SELF_RELIANCE_zscore_dummy', 'SOCIABILITY_zscore_dummy', 'SOCIAL_CONTACT_zscore_dummy', 'STRESS_TOLERANCE_zscore_dummy', \
    'TEAM_ORIENTATION_zscore_dummy', 'TOUGH_MINDEDNESS_zscore_dummy', 'VERBAL_REASONING_zscore_dummy']
    
    Population_Dummy_coded_Zscored_Headers_PPI2 = ['z_ACCEPTANCE_OF_AUTHORITY_dummy', 'z_AMBITION_dummy', 'z_ANALYTICAL_dummy',\
     'z_ASSERTIVENESS_dummy', 'z_ATTENTION_TO_DETAILS_dummy', 'z_BUSINESS_ATTITUDE_dummy', 'z_CHANGE_ORIENTATION_dummy', \
     'z_COMPETITIVE_FIERCENESS_dummy', 'z_CONFIDENCE_dummy', 'z_CONSCIENTIOUSNESS_dummy', 'z_COOPERATIVENESS_dummy', \
     'z_CREATIVITY_dummy', 'z_DISCIPLINE_dummy', 'z_EMOTIONAL_CONSISTENCY_dummy', 'z_ENERGY_dummy', 'z_FLEXIBILITY_dummy', \
     'z_INSIGHT_INTO_OTHERS_dummy', 'z_JOB_ATMOSPHERE_dummy', 'z_LEADERSHIP_IMPACT_dummy', 'z_MENTAL_FLEXIBILITY_dummy', \
     'z_NEED_FOR_RECOGNITION_dummy', 'z_NUMERICAL_REASONING_dummy', 'z_OBJECTIVITY_dummy', 'z_OPTIMISM_dummy', \
     'z_ORGANIZATIONAL_STRUCTURE_dummy', 'z_ORGANIZATIONAL_TENDENCY_dummy', 'z_PACE_dummy', 'z_PEOPLE_ORIENTATION_dummy', \
     'z_PRACTICAL_dummy', 'z_REALISTIC_THINKING_dummy', 'z_REFLECTIVE_dummy', 'z_RISK_TAKER_dummy', 'z_SELF_RELIANCE_dummy', \
     'z_SOCIABILITY_dummy', 'z_SOCIAL_CONTACT_dummy', 'z_STRESS_TOLERANCE_dummy', 'z_TEAM_ORIENTATION_dummy', 'z_TOUGH_MINDEDNESS_dummy',\
     'z_VERBAL_REASONING_dummy']
    
    Assessment_Dummy_column = lambda x: x > 4
    
    Sample_Assessment_outlier_dummy_code_columns['Sum of Sample Dependent Dimension Outliers'] = Series(Sample_Assessment_outlier_dummy_code_columns.ix[:,Sample_Dummy_coded_Zscored_Headers_PPI2].sum(axis = 1))
    Sample_Assessment_outlier_dummy_code_columns['Removal - Sample Dependent Assessment Outlier = 1'] = Series(Sample_Assessment_outlier_dummy_code_columns.ix[:,Sample_Dummy_coded_Zscored_Headers_PPI2].sum(axis = 1).apply(Assessment_Dummy_column),dtype=np.int32)
    
    Population_Assessment_outlier_dummy_code_columns['Sum of Population Dependent Dimension Outliers'] = Series(Population_Assessment_outlier_dummy_code_columns.ix[:,Population_Dummy_coded_Zscored_Headers_PPI2].sum(axis = 1))
    Population_Assessment_outlier_dummy_code_columns['Removal - Population Dependent Assessment Outlier = 1'] = Series(Population_Assessment_outlier_dummy_code_columns.ix[:,Population_Dummy_coded_Zscored_Headers_PPI2].sum(axis = 1).apply(Assessment_Dummy_column),dtype=np.int32)
    
    data_match = data_match.join(Sample_Assessment_outlier_dummy_code_columns[['Sum of Sample Dependent Dimension Outliers', 'Removal - Sample Dependent Assessment Outlier = 1']], rsuffix= '_y')
    data_match = data_match.join(Population_Assessment_outlier_dummy_code_columns[['Sum of Population Dependent Dimension Outliers', 'Removal - Population Dependent Assessment Outlier = 1']], rsuffix = '_y') 
    
    #Export to file to merge with Data file into a Master file
    #******************************************************************************    
    full_data = spin_master.join(data_match, rsuffix='_y')
    full_data['Performance Type'] = ''
    full_data['Set Type'] = 'Training'
    full_data['Overall Performance Rating'] = full_data['Item Avg']
    full_data = full_data.rename(columns={'FIRST_NAME': 'Match First', \
    'LAST_NAME': 'Match Last', 'LAST_FOUR_SSN': 'Match SSN'})
       
    master_tab_headers = ['PA ID', 'Match First', 'Match Last', 'Match Email', 'Match SSN', 'Performance Type', \
    'Set Type', tenure_label, 'Overall Performance Rating']
    
    data5 = full_data.ix[:,master_tab_headers]
       
    end_item_location = spin_master.columns.get_loc('Item Avg')
    data6 = data5.join(spin_master.ix[:,19:(end_item_location+6)], rsuffix= '_y')
    #data 6 is to append from item 1 through any supplemental items.
    #this is why we had to work backwards from the location of Item Avg
    #Item Avg should not be displayed here though. its just a reference point
       
    master_tab_headers2 = ['Job Title', 'Hire Date', 'Random ID', 'Ratee First Name', 'Ratee Last Name',\
    'Ratee Unique ID', 'Survey Group', 'Geo Level 1', 'Geo Level 2', 'Geo Level 3', 'Geo Level 4', 'Rater First Name',\
    'Rater Last Name', 'Rater Unique ID', 'Ratee Status']
    
    data7 = data6.join(full_data.ix[:,master_tab_headers2], rsuffix= '_y')
    data8 = data7.join(full_data.ix[:,Headers_PPI2], rsuffix= '_y')
    data9 = data8.join(full_data.ix[:,Quality_control_headers], rsuffix= '_y')
    
    data9['Removal - Not Matched = 1'] = Series(data9['PA ID'].isnull(),dtype=np.int32)
    
    #this can be built to hold all the removal headers
    master_tab_dummyheaders =['Removal - Quality Control = 1', 'Removal - Missing tenure data = 1', tenure_rem_label,\
    'Removal - Completely missing performance data = 1', 'Removal - Partially missing performance data = 1', 'Removal - Lack of Rater Confidence = 1',\
     'Removal - Sample Dependent Assessment Outlier = 1', 'Removal - Population Dependent Assessment Outlier = 1']
    
    data10 = data9.join(full_data.ix[:,master_tab_dummyheaders], rsuffix= '_y')
    #Below we fill any misising cells with zeros
    data10[master_tab_dummyheaders] = data10[master_tab_dummyheaders].fillna(0)
    
    data11 = data10
    final_removal_headers = ['Removal - Not Matched = 1'] + master_tab_dummyheaders
    data11['Final Sample Code'] = data11.ix[:,final_removal_headers].sum(axis= 1)
    Final_Data = data11[data11['Final Sample Code']==0]
    Final_Data = Final_Data.drop('Final Sample Code', 1)
    data10 = data10.drop('Final Sample Code', 1)
   
    
    '''MODELLING SECTION'''
    '''section has been omitted until sklearn is verified'''
    '''END MODELLING SECTION'''
    
    #appears as a collapsible frame on the page merge_and_master.html
    final_final_headers = Final_Data.columns[0:9].tolist()
    
    context['final_final_data'] = Final_Data[final_final_headers].to_html(index=False,na_rep='')
    context['col_headers'] = headerpacker(data10)
    context['data10'] = data10.to_json()
    context['in_name'] = in_name    
    
    
    '''SPECIFICALLY FOR CSO BLURB'''
    
    cso_removal_headers = ['Removal - Not Matched = 1',\
     'Removal - Completely missing performance data = 1',\
     'Removal - Partially missing performance data = 1',\
     'Removal - Missing tenure data = 1',\
     tenure_rem_label,\
     'Removal - Lack of Rater Confidence = 1',\
     'Removal - Quality Control = 1',\
     'Removal - Sample Dependent Assessment Outlier = 1',\
     'Removal - Population Dependent Assessment Outlier = 1']
    
    cso_removal_bullet_tags =  [' with missing assessment data',\
     ' with completely missing performance data',\
     ' with partially missing performance data',\
     ' with missing tenure data',\
     ' with insufficient tenure',\
     ' with poor rater confidence',\
     ' with QC issues in the assessment',\
     ' assessment outliers (sample)',\
     ' assessment outliers (population)']
    
    remdata = data10[cso_removal_headers]
    
    cso_actual_bullets = []
    
    remdata_temp = remdata
    
    for i in range(0,len(cso_removal_headers)):
        if remdata_temp[cso_removal_headers[i]].sum() == 0:
            next
        else:          
           cso_actual_bullets = \
           cso_actual_bullets + ['{} {}'.format(int(remdata_temp[cso_removal_headers[i]].sum()), cso_removal_bullet_tags[i])]
           
           remdata_temp = remdata_temp[remdata_temp[cso_removal_headers[0:i+1]].sum(axis=1)==0]
    
    
    time_format = "%H:%M:%S"

    end_time_sec = int(end_time.split('.')[0].split(":")[0])*60*60 + int(end_time.split('.')[0].split(":")[1])*60 + int(end_time.split('.')[0].split(":")[2])
    start_time_sec = int(start_time.split('.')[0].split(":")[0])*60*60 + int(start_time.split('.')[0].split(":")[1])*60 + int(start_time.split('.')[0].split(":")[2])
    
    beat_time_sec = end_time_sec - start_time_sec
    
    if beat_time_sec < 60:
        beat_time_seconds = beat_time_sec
        beat_time_minutes = 0
        beat_time_hours = 0
    elif beat_time_sec < (60*60):
        beat_time_hours = 0
        beat_time_minutes = beat_time_sec / 60
        try:
            beat_time_seconds = beat_time_sec % 60
        except:
            beat_time_seconds = 0
    else:
        beat_time_hours = beat_time_sec / (60*60)
        if beat_time_sec % 60*60 == 0:
            beat_time_minutes = 0
            beat_time_seconds = 0
        else:
            beat_time_minutes = beat_time_sec % 60*60
            if beat_time_sec % 60 == 0:
                beat_time_seconds = 0
            else:
                beat_time_seconds = (beat_time_sec % 60*60) % 60

    
    if beat_time_minutes < 10:
        beat_time_minutes = '0{}'.format(beat_time_minutes)
    else:
        pass
    if beat_time_seconds < 10:
        beat_time_seconds = '0{}'.format(beat_time_seconds)
    else:
        pass

    beat_time = "{}:{}:{}".format(beat_time_hours,beat_time_minutes,beat_time_seconds)
    #print beat_time
        
    context['cso_actual_bullets'] = cso_actual_bullets
    context['start_sample'] = len(spin_master)
    context['final_sample'] = len(Final_Data)
    context['metric_avg'] = "Average score: {}".format(("%.2f" % Final_Data['Item Avg'].mean()))    
    context['metric_min'] = "Min: {}".format(("%.2f" % Final_Data['Item Avg'].min()))
    context['metric_max'] = "Max: {}".format(("%.2f" % Final_Data['Item Avg'].max()))
    
    #for beat_the_best
    context['beat_time'] = beat_time
    context['beat_time_sec'] = beat_time_sec #actual seconds of beat time
    context['beat_hours'] = beat_time.split(":")[0] #string formatted for clock like display
    context['beat_minutes'] = beat_time.split(":")[1] #string formatted for clock like display
    context['beat_seconds'] = beat_time.split(":")[2] #string formatted for clock like display
        
                
    return render(request, 'twister/merge_and_master.html', context)

#out of merge_and_master, there are two icons: claim prize and beat the best
#claim prize exports a randomly chosen item from the static/dlc folder

def click_spin_export(request):
             
    in_name = str(request.POST.get('in_name'))
    
    col_headers = pd.read_json(request.POST.get('col_headers'))
    col_headers.sort('order',inplace=True)
    col_headers = col_headers.header.tolist()

    spin_master = pd.read_json(request.POST.get('master_data')) 
    spin_master = spin_master[col_headers]
               
    xls_out = "SpinMaster({}).xls".format(in_name.rstrip(".csv"))   
        
            
    xlwt_writer = pd.io.excel.get_writer('xlwt')
    writer = xlwt_writer("test.xls") #make pandas happy
     
    #writer = pd.ExcelWriter("temp.xls", engine='xlsxwriter')
    io_name = StringIO.StringIO()
    
    writer.book.name  = io_name
    writer.path  = io_name
    spin_master.to_excel(writer,sheet_name='SpinMaster',index=False,merge_cells=False,na_rep='')
    writer.save()
    
    xls_output = io_name.getvalue()    
            
    response = HttpResponse(xls_output,content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(xls_out)
    return response



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


#the profile creation match export template
def export_empty_match(request):
    # Create the HttpResponse object with the appropriate CSV header.

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="/empty_match.csv"'

    writer = csv.writer(response)
    
    header_row = ["PA ID","FIRST_NAME","LAST_NAME","EMAIL","LAST_FOUR_SSN","COMPANY_CANDIDATE_ID",\
    "COMPANY_CANDIDATE_CODE","DATE_IN_POSITION","SET_TYPE","ASSESSMENT_DATE","Core Dimension Composition Type",\
    "ACCEPTANCE_OF_AUTHORITY","AMBITION","ANALYTICAL","ASSERTIVENESS","ATTENTION_TO_DETAILS","BUSINESS_ATTITUDE",\
    "CHANGE_ORIENTATION","COMPETITIVE_FIERCENESS","CONFIDENCE","CONSCIENTIOUSNESS","COOPERATIVENESS","CREATIVITY",\
    "DISCIPLINE","EMOTIONAL_CONSISTENCY","ENERGY","FLEXIBILITY","INSIGHT_INTO_OTHERS","JOB_ATMOSPHERE","LEADERSHIP_IMPACT",\
    "MENTAL_FLEXIBILITY","NEED_FOR_RECOGNITION","NUMERICAL_REASONING","OBJECTIVITY","OPTIMISM","ORGANIZATIONAL_STRUCTURE",\
    "ORGANIZATIONAL_TENDENCY","PACE","PEOPLE_ORIENTATION","PRACTICAL","REALISTIC_THINKING","REFLECTIVE","RISK_TAKER",\
    "SELF_RELIANCE","SOCIABILITY","SOCIAL_CONTACT","STRESS_TOLERANCE","TEAM_ORIENTATION","TOUGH_MINDEDNESS","VERBAL_REASONING",\
    "PPI_TOTAL_ITEM_MINUTES","PPI_MINUTES","FALSIFICATION","CONSISTENCY","CLICK_THROUGH","SEQUENCE","LCS_LENGTH","Last 4 SSN","Random ID","Ratee Unique ID"]
 
    writer.writerow(header_row)
    
    return response


def full_docs(request):
     context = dict()
     z = "Full docs"
     context["print_y"] = z       
            
     return render(request, 'twister/full_docs.html', context)
    

def headerpacker(dataframe):
    temp_header_array = dataframe.columns.values
    
    order_list = []
    header_list = []
    
    for i in range(0,len(temp_header_array)):
        order_list = order_list + [i]
        header_list = header_list + [temp_header_array[i]]
    
    header_frame = pd.DataFrame({'order':order_list,'header':header_list})

    return header_frame.to_json()


def shorten_labels(list): #used to make item-corr table row labels more readable
    long_labels = list
    
    short_heads = []
    for head in long_labels:
        try:
            short_heads = short_heads + [str(head)[:25]]
        except:
            short_heads = short_heads + head

    return short_heads


def click_final_export(request):
             
    in_name = str(request.POST.get('in_name'))
    
    col_headers = pd.read_json(request.POST.get('col_headers'))
    col_headers.sort('order',inplace=True)
    col_headers = col_headers.header.tolist()

    data10 = pd.read_json(request.POST.get('data10')) 
    data10 = data10[col_headers]
               
    xls_out = "FinalResults({}).xls".format(in_name.rstrip(".csv"))      
            
    xlwt_writer = pd.io.excel.get_writer('xlwt')
    writer = xlwt_writer("test.xls") #make pandas happy
     
    io_name = StringIO.StringIO()
    
    writer.book.name  = io_name
    writer.path  = io_name
    data10.to_excel(writer,sheet_name='Master',index=False,merge_cells=False,na_rep='')
    writer.save()
    
    xls_output = io_name.getvalue()    
            
    response = HttpResponse(xls_output,content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(xls_out)
    return response


def compute_cronbachs(k,data_spinalysis):
        
    alpha_without_item_list = []
    k_without = k - 1
    data_items = data_spinalysis.ix[:,18:(18+k)]
    col_list = data_items.columns.tolist()    
    item_summary = data_items.describe()    
    
    for i in range(0,len(col_list)):
        
        list_without = data_items.columns.tolist()
        list_without.remove(list_without[i])
        data_sub = data_items[list_without]
        corrs_items_without = data_sub.corr()
        sum_corrs_without = corrs_items_without.sum().sum()
        r_bar_lower_without = (sum_corrs_without-k_without) / (k_without*(k_without-1))               
        alpha_without_item = k_without*r_bar_lower_without / (1+(k_without-1)*r_bar_lower_without)
        alpha_without_item_list = alpha_without_item_list + [alpha_without_item]  
    
    alpha_wo_frame = pd.DataFrame(alpha_without_item_list).T
    alpha_wo_frame = alpha_wo_frame.rename(index={0:'alpha w item removed'})
    alpha_wo_frame.columns = item_summary.columns
    new_summary = pd.concat([item_summary,alpha_wo_frame])    
    
    return new_summary


def scoreboard(request):
    context = dict()
    beat_time = str(request.POST.get('beat_time'))
    
    
    in_name = str(request.POST.get('in_name'))
    start_sample = str(request.POST.get('start_sample'))
    final_sample = str(request.POST.get('final_sample'))  
    
    
    scoreboard_input_data = os.getcwd() + '/twister/templates/twister/scoreboard_stock.csv'
    ifile = open(scoreboard_input_data, "r+")    
    top_scores = pd.read_csv(ifile) 
    ifile.close()
    
    version_now = "'i don't want to leave no mysteries - Dave Chappelle'"   
    
    top_scores['old_new'] = 0
    beat_score = {'Beat Time':beat_time,'Data':in_name,'Field Sample':start_sample,'Pure Sample':final_sample, 'old_new':1}      
    all_scores = top_scores.append(beat_score,ignore_index=True)  
    
    #Don't overwrite Beat Time, use another temp column bc formatting timedelta is a nightmare
    #use it to sort, then delete it
    
    beat_list = all_scores['Beat Time'].values
    sec_list = []
    for i in beat_list:
        hs = int(i.split(':')[0].split(',')[-1])*60*60
        ms = int(i.split(':')[1])*60
        s = int(i.split(':')[2])
        sec_list = sec_list + [hs+ms+s]

    
    all_scores['Beat Time_deleteme'] = sec_list
    all_scores.sort(columns=['Beat Time_deleteme'],inplace=True)
    
    i = 0
    beat_rank = 7
    for i in range(0,len(all_scores.old_new.values)):
        if all_scores.old_new.values[i] == 1:
            beat_rank = i + 1

    
    del all_scores['Beat Time_deleteme'], sec_list, all_scores['old_new']
    #comment based on beat_time's ranking
    
    if beat_rank == 1:
        beat_comment = 'You are the Best! The Twister gods are pleased.'
    elif beat_rank == 2:
        beat_comment = 'Great time! Nearly the best.'
    elif beat_rank == 3:
        beat_comment = 'A valiant effort! You have made the top three.'
    elif beat_rank == 4:
        beat_comment = 'Congratulations! You have a top time.'
    elif beat_rank == 5:
        beat_comment = 'Way to go! You are on the board.'
    else:
        beat_comment = 'The Twister gods demand more sacrifice.'       
    
    all_scores.drop_duplicates(inplace=True)
    top_scores = all_scores.iloc[:5]
    
    ifile = open(scoreboard_input_data, "w")    
    all_scores.to_csv(ifile,index=False) 
    ifile.close()  
    
    
    context['beat_comment'] = beat_comment
    context['top_scores'] = top_scores.to_html(index=False)
    
    context['in_name'] = in_name
    context['version_now'] = version_now
    
    context['start_sample'] = start_sample
    context['final_sample'] = final_sample
    context['beat_time'] = beat_time
    context['beat_hours'] = beat_time.split(":")[0]
    context['beat_minutes'] = beat_time.split(":")[1]
    context['beat_seconds'] = beat_time.split(":")[2]
        
    return render(request, 'twister/scoreboard.html', context)


def prizes(request): #choose from dlc directory and serve to user
    
    context = dict()
    
    '''
    try:
        with open(valid_image, "rb") as f:
            return HttpResponse(f.read(), content_type="image/jpeg")
    except IOError:
        red = Image.new('RGBA', (1, 1), (255,0,0,0))
        response = HttpResponse(content_type="image/jpeg")
        red.save(response, "JPEG")
        return response
    #response = HttpResponse(xls_output,content_type='application/vnd.ms-excel')
    #response['Content-Disposition'] = 'attachment; filename="{}"'.format(xls_out)
    '''
    
    return render(request, 'twister/prizes.html', context)
