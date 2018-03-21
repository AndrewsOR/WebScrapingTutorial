# -*- coding: utf-8 -*-
"""
Created on Tue Mar 13 08:08:32 2018

@author: jandrews

1. Get list of region pages from home url
2. For each region page, get the table
3. Combine the tables
4. Write the combined table to CSV

The home page content we want looks like this:
    
  <select id="stateSelect" class="hsbHeaderSelect" style="position:relative;float:right;top:-2px">
   <option value="#">Make a Selection</option>
   <option value="/report/top-financial-advisors/1000/alabama/2018">Alabama</option>
   <option value="/report/top-financial-advisors/1000/alaska/2018">Alaska</option>
   ...
  </select>

The table content we want looks like this:
    <table>
        <thead>
        <tr class="tableHeaderMeta">
        <th class="leftAligned borderRight" colspan="5"> </th>
        <th class="borderRight" colspan="6">Customers</th>
        <th colspan="4"> </th>
        </tr>
        <tr class="tableHeader">
            <th class="marketDelta" colspan="2" style="padding:0px 5px 0px 0;"><b>Rank</b></th>
            <th class="marketDelta" colspan="3" style="padding:0px 5px 0px 0;"> </th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;"><b>   Individuals   </b></th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;"><b>High<br/>Net Worth</b></th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;"><b>Ultra-High<br/>Net Worth</b></th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;" valign="bottom"><b>Founda-</b></th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;" valign="bottom"><b>Endow-</b></th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;" valign="bottom"><b>Institu-</b></th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;"><b>Total<br/>Asset</b></th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;"><b>Typical<br/>Account</b></th>
            <th class="marketDelta" style="padding:0px 5px 0px 0;"><b>Typical<br/>Net Worth</b></th>
        </tr>
        <tr class="tableHeader">
            <th class="marketDelta" style="padding:0px 5px 4px 0;"><b>'18</b></th>
            <th class="marketDelta" style="padding:0px 5px 4px 0;">'17</th>
            <th class="marketName" style="padding:0px 5px 4px 0;"><b>Name</b></th>
            <th class="marketName" style="padding:0px 5px 4px 0;"><b>Firm</b></th>
            <th class="marketName" style="padding:0px 5px 4px 0;"><b>Location</b></th>
            <th class="marketDelta" style="padding:0px 5px 4px 0;">(Up to $1mil)</th>
            <th class="marketDelta" style="padding:0px 5px 4px 0;">($1-10 mil)</th>
            <th class="marketDelta" style="padding:0px 5px 4px 0;">($10 mil+)</th>
            <th class="marketName" style="padding:0px 5px 4px 0;"><b>tions</b></th>
            <th class="marketName" style="padding:0px 5px 4px 0;"><b>ments</b></th>
            <th class="marketName" style="padding:0px 5px 4px 0;"><b>tional</b></th>
            <th class="marketDelta" style="padding:0px 5px 4px 0;">($mil)</th>
            <th class="marketDelta" style="padding:0px 5px 4px 0;">($mil)</th>
            <th class="marketDelta" style="padding:0px 5px 4px 0;">($mil)</th>
        </tr>
        </thead>
        <tbody>
        <tr class="alt">
            <td class="marketDelta">1</td>
            <td class="marketDelta">2</td>
            <td class="marketName"><b>Tony  Smith</b></td>
            <td class="marketName">UBS Financial Svcs</td>
            <td class="marketName">Birmingham, AL</td>
            <td class="marketDelta"></td>
            <td class="marketDelta"><img src="/img/black_bullet.gif"/></td>
            <td class="marketDelta"><img src="/img/black_bullet.gif"/></td>
            <td class="marketName"></td>
            <td class="marketName"></td>
            <td class="marketName"></td>
            <td class="marketDelta">3209</td>
            <td class="marketDelta">50</td>
            <td class="marketDelta">100</td>
        </tr>
    ...etc..


"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from unicodedata import normalize
import re

HOME_DOMAIN = 'http://www.barrons.com'
HOME_DIR = '/report/top-financial-advisors/1000/2018'
OUT_CSV = '/Users/jandrews/workspace/barrons_financial_advisors.csv'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
           'AppleWebKit/537.36 (KHTML, like Gecko) '
           'Chrome/50.0.2661.102 Safari/537.36'}

def getSoup(url, headers):
    resp = requests.get(url, headers=headers)
    print('Requested {} returning status {}\n'.format(url, resp.status_code))
    if resp.status_code==200:
         soup = BeautifulSoup(resp.text, 'lxml')
    else: 
        soup = None
        print('Unable to return content from: {}\n'.format(url))
    return soup

def getRegionDirs(homeDomain, homeDir, headers):
    soup = getSoup(homeDomain + homeDir, headers)
    opts = soup.find('select',{'id':'stateSelect'})
    return [x['value'] for x in opts.find_all('option') 
            if x and x['value'] != '#']   
    
def getRegionTable(homeDomain, regionDir, headers):
    soup = getSoup(homeDomain + regionDir, headers)
    return soup.find('table')

def getTableHeaders(table):
    """The table headers are formatted poorly,
        with some headers spanning multiple columns and rows.
        """
    headerTags = [t.find_all('th') for t in table.find_all('tr',{'class':'tableHeader'})]
    colspans = [ [int(item['colspan']) if item.has_attr('colspan') else int(1) for item in sublist] for sublist in headerTags]
    # replace non-breaking spaces
    headers = [ [normalize('NFKD',item.get_text()).strip() for item in sublist] for sublist in headerTags]
    headerRows = [np.repeat(i,j).tolist() for i,j in zip(headers,colspans)]
    return ["{} {}".format(a,b).strip().replace('- ','') for a,b in zip(*headerRows)] #.encode('utf-8')

def getTableData(table, colNames = None):
    bodyTags = [t.find_all('td') for t in table.find('tbody').find_all('tr')]
    
    records = [ [normalize('NFKD',item.string).strip() if item.string  #.encode('utf-8')
                   else 'Y' if item.find('img')
                   else ''
                   for item in sublist] for sublist in bodyTags]   
    return pd.DataFrame.from_records(records, columns=colNames)

def getRegionData(homeDomain, regionDir, headers):
    table = getRegionTable(homeDomain, regionDir, headers)
    data = getTableData(table, colNames = getTableHeaders(table))
    data['region'] = re.findall('/1000/(\w+)/2018',regionDir)[0]
    return data

if __name__ == "__main__":
    data = pd.concat([getRegionData(HOME_DOMAIN, path, HEADERS) for path in
                        getRegionDirs(HOME_DOMAIN, HOME_DIR, HEADERS)])
    out = open(OUT_CSV,'w',encoding='utf8')
    print('Writing {} results to: {}'.format( len(data.index), OUT_CSV))
    data.to_csv(out, index=False)
    out.close()
