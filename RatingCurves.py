#Script:RatingCurves.py
#       This script contains functions for processing manual streamgauging  
#       data. The inputs are the columns of the Rating_Curve_Calculations.xlsx.
#       The outputs are datafiles merged by location with flow calculated and 
#       several exploratory figures. 
#Created by: Julia Signell
#Date created: 2014-10-28
#Date modified:2015-03-28

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xlrd
import datetime as dt

usr = 'PELuser'
FILEDIR = "C:/Users/%s/Dropbox (PE)/KenyaLab/Data/Streamflow/"%usr
OTT_FILE = "OTT_Data_All_stations.xlsx"
RC_FILE = "RatingCurves/Rating_Curve_Calculations.xlsx"

def OTT_read(xl,site):
    #read in all of the OTT depth and temperature data 
    df = pd.read_excel(xl.io,site,skiprows=2,parse_dates=0,index_col=0,
                       usecols=[0,1,2],header=None,
                       names=['date_time','%s_depth'%site,'%s_temp'%site]) 
    return df

def make_OTT_df(FILEDIR,OTT_FILE):
    #make a list of dataframes with one for each site
    xl = pd.ExcelFile(FILEDIR + OTT_FILE)
    sites = xl.sheet_names
    
    df_list = [OTT_read(xl,site) for site in sites]
    return sites,df_list

def RC_read(xl,site,cols):
    #read in all manually gathered flow data and round times to 5 min
    df = pd.read_excel(xl.io,'Rating Curves',skiprows=1,usecols=cols,
                       names=['date','time','%s_flow'%site],
                       parse_dates=[[0,1]],index_col=0)
    df = df.resample('5min')
    df = df.dropna(how='any')
    return df

def make_RC_df(FILEDIR,RC_FILE):
    #open the rating curve file and take the names of the sites along with 
    #a list of dataframes with one for each site
    workbook = xlrd.open_workbook(FILEDIR + RC_FILE)
    sheet = workbook.sheet_by_name('Rating Curves')
    sites = [str(sheet.cell(0, col).value) for col in range(sheet.ncols)]
    sites = filter(None,sites)

    xl = pd.ExcelFile(FILEDIR + RC_FILE)
    col_list = [[k,k+1,k+3] for k in range(1,len(sites)*4,4)]
    df_list = [RC_read(xl,sites[i],col_list[i]) for i in range(len(sites))]
    
    return sites,df_list

def make_df(sites_OTT,df_list_OTT,sites_RC,df_list_RC):
    #combine manual and OTT dataframes and return a list of dataframes as well 
    #as a large complete dataframe
    df_list = []
    for i in range(len(sites_OTT)):
        for k in range(len(sites_RC)):
            if sites_OTT[i] == sites_RC[k]:
                df_RC =df_list_OTT[i].join(df_list_RC[k],how='inner') 
                df_list.append((sites_OTT[i],df_RC))
                # this is a list of (site,df_RC) tuples
    df = df_list_OTT[0]
    for i in range(1,len(df_list_OTT)):
        df = df.join(df_list_OTT[i],how='outer')
    df = df.ix[0:-1,:]
    df = df.dropna(how='all')
        
    return df_list,df

def make_RC(site,df_RC,df):
    #calculate the fit for each site's rating curve, save plot, and dataframe
    #with calcuated flow at all times where there is OTT depth
    fit = np.array
    fit = np.polyfit(df_RC['%s_depth'%site],df_RC['%s_flow'%site],2)
    
    df_RC.plot(x = 0, y = 2, kind = 'scatter', figsize = (10,6))
    x = np.array(range(0,int(max(df_RC['%s_depth' % site]))+5,1))
    y = fit[0]*x**2 + fit[1]*x + fit[2]
    plt.plot(x, y)
    plt.xlim(min(df_RC['%s_depth'%site])-5, max(df_RC['%s_depth'%site])+5)
    plt.ylim(ymin = 0)
    plt.xlabel('%s Depth [cm]' % site)
    plt.ylabel('%s Flow [m^3/s]' % site)
    plt.title(('%s Rating Curve : flow = %f *x^2 + %f*x + %f'%
              (site,float(fit[0]),float(fit[1]),float(fit[2]))))
    plt.savefig(FILEDIR + "RatingCurves/Rating_Curve_%s.jpg"%site)
    plt.clf()
    
    x = df['%s_depth'%site]
    df['%s_flow'%site] = fit[0]*x**2 + fit[1]*x + fit[2]
    df.loc[df['%s_flow'%site]<0,'%s_flow'%site] = 0
    
    return df

def save_file(df,FILEDIR):
    #create files of all the data from the OTTs and calculated flow at each 
    #site at different frequencies for ease of access. Also make a summary 
    #file with the percentiles. 
    df.sort(axis=1,inplace=True)
    df = df.dropna(how='all')
    for freq in ['D','H','5min']:
        df_freq = df.resample(freq)
        df_freq.to_csv(FILEDIR + 'Stream_Discharge_All_%s.csv'%freq,
                       date_format='%Y-%m-%d %H%M')
    summary = df_freq.describe(percentiles = (.1,.2,.3,.4,.5,.6,.7,.8,.9))
    summary.to_csv(FILEDIR + 'Stream_Discharge_All_summary.csv')
    
def make_dfh_flow(df):
    #make an horly dataframe with just the flows
    df = df.dropna(how = 'all')
    dfh = df.resample('60min')
    dfh_flow = pd.DataFrame(index = dfh.index)
    for i in range(len(dfh.columns)):
        if 'flow' in dfh.columns[i]:
            dfh_flow[dfh.columns[i]] =dfh[dfh.columns[i]]
    return dfh_flow

def make_plots(dfh_flow,FILEDIR):
    #make some quick plots to get a sense of the data and save them
    dfh_flow.plot(figsize = (18,6),colormap='rainbow')
    plt.ylabel('Calculated Discharge [m^3/s]')
    plt.xlabel(' ')
    legend = [columns.partition('_')[0] for columns in dfh_flow.columns]
    plt.legend(legend)
    plt.savefig(FILEDIR + 'Stream_discharge_all.jpg')
    plt.clf()

    dfh_flow.plot(figsize = (18,6),colormap='rainbow')
    plt.ylabel('Calculated Discharge [m^3/s]')
    plt.xlabel(' ')
    plt.ylim(0,50)
    plt.legend(legend)
    plt.savefig(FILEDIR + 'Stream_discharge_without_highs.jpg') 
    plt.clf()
    
def main():
    #this is where all the functions are called with the times printed at the 
    #beginning and end so that run-time can be easily monitored 
    print dt.datetime.now()
    sites_OTT,df_list_OTT = make_OTT_df(FILEDIR,OTT_FILE)
    sites_RC,df_list_RC = make_RC_df(FILEDIR,RC_FILE)
    df_list,df = make_df(sites_OTT,df_list_OTT,sites_RC,df_list_RC)
    for site,df_RC in df_list:
        if df_RC.empty == False:
            df = make_RC(site,df_RC,df) 
    save_file(df,FILEDIR)
    dfh_flow = make_dfh_flow(df)
    make_plots(dfh_flow,FILEDIR)
    print 'done!'
    print dt.datetime.now()
      
if __name__ == '__main__':
    main()