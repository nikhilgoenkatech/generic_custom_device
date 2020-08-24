import os
import io
import sys  
import json
import time
import logging
import certifi
import smtplib
import traceback
import requests
import datetime
from constant import *
sys.path.append("")

class tenantInfo:
   def __init__(self):
     self.tenant_url = ""
     self.tenant_get_token = ""
     self.tenant_post_token = ""
     self.name = ""

json_data = {}
json_data["series"] = []
#json_data["type"]="USQL data"
#property_var = {}
#property_var['Property']="USQL data sent back through API"
#json_data["properties"]=property_var
#------------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to make API call using the token defined in constant.py
# Returns the json object returned using the API call 
#------------------------------------------------------------------------------
def dtApiQuery(logger, endpoint, tenant_info, URL=""):
  try: 
    logger.info("In dtApiQuery")
    logger.debug ("dtApiQuery: endpoint = %s", endpoint)
    buffer = io.BytesIO()

    if URL == "":
      URL = tenant_info.tenant_url + USQL_QUERY
   
    #print "\n\n\n" + URL 
    endpoint = endpoint.replace(" ", "%20")
    endpoint = endpoint.replace("=", "%3D")
    endpoint = endpoint.replace("\"", "%22")

    endpoint = URL + "query=" + endpoint + "&explain=false" 
    #print "\n\n\n NEXT"
    #print endpoint
    get_param = {'Accept':'application/json; charset=utf-8', 'Authorization':'Api-Token {}'.format(tenant_info.tenant_get_token)}
    config_post = requests.get(endpoint, headers = get_param)
    #print "\n\n\n VALUE"
    print (config_post.text)
    #c = pycurl.Curl()
    ##print str(URL) + "query=" + str(endpoint) + "&explain=false"
    #c.setopt(c.URL, URL + "query=" + str(endpoint) + "&explain=false")
    #c.setopt(pycurl.CAINFO, certifi.where())
    #c.setopt(c.HTTPHEADER, ['Authorization: Api-Token ' + tenant_info.tenant_get_token] )
    #c.setopt(pycurl.WRITEFUNCTION, buffer.write)
    #c.perform()
    #c.close()
    logger.info("Execution sucessfull: dtApiQuery")

  except Exception as e:
    traceback.print_exc()
    logger.error("Received exception while running dtApiQuery", str(e), exc_info = True) 

  finally:
    #return(buffer.getvalue().decode('UTF-8'))
    return(config_post.text)
#------------------------------------------------------------------------
# Author: Nikhil Goenka
# filename: the config file which the user would configure
#------------------------------------------------------------------------
def parse_config(filename):
  try:
    stream = open(filename)
    data = json.load(stream)
  except Exception:
    traceback.print_exc()
    print ("Exception encountered in parse_config function : %s ", str(e))
  finally:
    return data

#------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to call API and populate the excel file
#------------------------------------------------------------------------
def populate_tenant_details(logger, tenant, tenant_info):
  try:
    logger.info("In populate_tenant_details")
    logger.info("In populate_tenant_details %s ", tenant)

    tenant_info.tenant_url = tenant['tenant-URL'] 
    tenant_info.tenant_get_token = tenant['HTTP-GET-token']
    tenant_info.tenant_post_token = tenant['DT-POST-token']
    tenant_info.name = tenant['tenant-name']
  except Exception as e:
    traceback_print.exc()
    print ("Exception encountered while executing populate_tenant_details %s ", str(e))
  finally:
    return tenant_info 

#------------------------------------------------------------------------
# Author: Nikhil Goenka
#------------------------------------------------------------------------
def call_http_endpoint(logger, tenant_info, use_case):
  try:
    
    logger.info("In call_http_endpoint")
    query = use_case['http-endpoint']
    logger.debug("http_endpoint= %s", query)
    applicationIO = dtApiQuery(logger, query, tenant_info)
    applications = json.loads(applicationIO)

    epoch_time = time.mktime(datetime.datetime.now().timetuple()) * 1000

    if applications != "":
     values = applications["values"]

    dbnames = use_case['metric-dbname']
    if "," in dbnames:
      logger.debug("Encountered multiple values for single API call " + dbnames)
      dbnames = dbnames.split(',')

      for i in range(len(dbnames)):
       if values:
         value = values[0][i]
         print "SINGLE_VALUE ", value
         dbname = dbnames[i]
         print "dbname - ", dbname

       data_obj  = {}
       data_obj ['dataPoints'] = [[epoch_time,float(value)]]
       data_obj ["timeseriesId"] = dbname

       json_data["series"].append(data_obj)
    else:
       value = float(values[0][0])

       data_obj  = {}
       data_obj ['dataPoints'] = [[epoch_time,float(value)]]
       data_obj ["timeseriesId"] = dbnames 

       json_data["series"].append(data_obj)
     
    logger.info("Successful execution: fetch_sync_application")
    
  except Exception as e:
    traceback.print_exc()
    logger.fatal("Received exception while running call_http_endpoint", str(e), exc_info=True)

  finally:
    return json_data 

def createCustomDevice(logger, application, tenant_info, device_id):
  try:
    config_url = tenant_info.tenant_url + CREATE_CUSTOM_DEVICE + str(device_id)
    #config_url="https://stg99002.live.dynatrace.com/api/v1/entity/infrastructure/custom/idOfmyCustomDevice" + str(device_id) 
    post_param = {'Content-Type':'application/json; charset=utf-8', 'Authorization':'Api-Token {}'.format(tenant_info.tenant_post_token)}

    #print config_url
    #print post_param
    #create_custom_device_file = open("create_custom_device.json")
    #custom_device_details = json.load(create_custom_device_file)
   
    application_name = application["device-name"] 
    custom_device_details = {}

    if application["device-property"]["type"] != None and application["device-property"]["type"] != "":
      custom_device_details['type'] = application["device-property"]["type"]

    if application["device-property"]["properties"] != None and application["device-property"]["properties"] != "":
      custom_device_details['properties'] = {}
      custom_device_details['properties']['Property'] = application["device-property"]["properties"]

    if application["device-name"] != None and application["device-name"] != "":
      custom_device_details['displayName'] = application_name

    if application["device-property"]["ipAddresses"] != None and application["device-property"]["ipAddresses"] != "":
      for item in application["device-property"]["ipAddresses"]:
       try:
         custom_device_details["ipAddresses"].append(item)
       except KeyError as e:
         custom_device_details["ipAddresses"] = []
         custom_device_details["ipAddresses"].append(item)

    if application["device-property"]["listenPorts"] != None and application["device-property"]["listenPorts"] != "":
      for item in application["device-property"]["listenPorts"]:
       print " Reading listenPorts" + str(item)
       try:
         custom_device_details["listenPorts"].append(item)
       except KeyError as e:
         custom_device_details["listenPorts"] = []

    if application["device-property"]["tags"] != None and application["device-property"]["tags"] != "":
      for item in application["device-property"]["tags"]:
       try:
         custom_device_details["tags"].append(item)
       except KeyError as e:
         custom_device_details["tags"] = []

    if application["device-property"]["configURL"] != None and application["device-property"]["configURL"] != "":
      custom_device_details["configUrl"] = application["device-property"]["configURL"]

    if application["device-property"]["favicon"] != None and application["device-property"]["favicon"] != "":
      custom_device_details["favicon"] = application["device-property"]["favicon"]

    config_post = requests.post(config_url, data = json.dumps(custom_device_details), headers = post_param)
    if config_post.status_code != 200:
      logging.error('postConfigs: failed to create customDevice for ')
    else:
       logging.info('SUCCESS postConfigs status code for {0} '.format(application_name))
    #logger.info("")
    #print config_post.text

  except Exception, e:
    traceback.print_exc()
    logger.fatal("Received exception while running createCustomDevice", str(e), exc_info=True)

  finally:
    return config_url

def send_data_custom_device(logger, restpoint, json_data):
  try:
    logger.debug("In send_data_custom_device")
    post_param = {'Content-Type':'application/json; charset=utf-8', 'Authorization':'Api-Token {}'.format(tenant_info.tenant_post_token)}

    config_post = requests.post(restpoint, data = json.dumps(json_data), headers = post_param)
    if config_post.status_code != 200:
      logging.error('postConfigs: failed to send data %s %s', config_post.text, json.dumps(json_data))
    else:
      logging.debug('postConfigs: sent data succesfully %s %s', config_post.text, json.dumps(json_data))
     
  except requests.exceptions.RequestException as e:
    raise SystemExit(e)
    logger.fatal("Received exception while running send_data_custom_device ", str(e), exc_info=True)
     
  finally:
    return 
#------------------------------------------------------------------------
# Author: Nikhil Goenka
# Function to call API and populate the excel file
#------------------------------------------------------------------------

if __name__ == "__main__":
  try:
    while (1):
      flag = 0 #Flag to initialize the timeseries id
      filename = "config.json"
      data = parse_config(filename)
      
      logging.basicConfig(filename=data['log_file'],
                              filemode='a',
                              format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                              datefmt='%Y-%m-%dT%H:%M:%S.000',
                              level=logging.DEBUG)
      logger = logging.getLogger()
      tenants = data['tenant-details']

      applications = data['custom-device-details']
      for i in range(len(applications)):

        json_data["tags"] = []
        if applications[i]["device-property"]["tags"] != "":
         for tag in applications[i]["device-property"]["tags"]:
           json_data["tags"].append(tag)

        tmp_dic = {}
        tmp_dic["Property"]     = applications[i]["device-property"]["properties"]
        json_data["properties"] = tmp_dic

        json_data["type"] = applications[i]["device-property"]["type"]
        
        #create the custom device - can check in DB if the device is already present
        use_cases = applications[i]['metrics-details']

        tenant_info = tenantInfo()
        tenant_info = populate_tenant_details(logger, data['tenant-details'], tenant_info)

        device_id = applications[i]["device-id"]
        restpoint = createCustomDevice(logger, applications[i], tenant_info, device_id)
        if flag == 0:
          for k in range(len(use_cases)):
            timeSeriesURL = "https://stg99002.live.dynatrace.com/api/v1" + TIMESERIES_DEF
            #timeSeriesURL = tenant_info.tenant_url + TIMESERIES_DEF
            metrics_name = use_cases[k]["metric-dbname"]
            #print metrics_name 
            if "," in metrics_name:
              dbnames = metrics_name.split(",")
              displayNames = use_cases[k]["metric-displayname"].split(",")
              units = use_cases[k]["unit"].split(",")

              for l in range(len(dbnames)):
                #timeSeriesURL = "https://stg99002.live.dynatrace.com/api/v1" + TIMESERIES_DEF
                timeSeriesURL = tenant_info.tenant_url + TIMESERIES_DEF
                timesSeriesURL = timeSeriesURL + dbnames[l]
                displayName = displayNames[l]

                timeSeriesURL = timeSeriesURL + dbnames[l] 
          
                timeseries_def = {}
                timeseries_def["displayName"] = displayName 
                timeseries_def["types"]=[]
                timeseries_def["types"].append(applications[i]["device-property"]["type"])
                timeseries_def["unit"] = units[l]
                post_param = {'Content-Type':'application/json; charset=utf-8', 'Authorization':'Api-Token {}'.format(tenant_info.tenant_post_token)}
                try:
                  config_post = requests.put(timeSeriesURL, data = json.dumps(timeseries_def), headers = post_param)
                except requests.exceptions.HTTPError as err:
                  raise SystemExit(err)
                if config_post.status_code != 200:
                  logging.error('postConfigs: failed to create timeseries for %s ', dbnames[l])
                else:
                   logging.info('SUCCESS postConfigs status code for {0} '.format(dbnames[l]))
            else:
              timeSeriesURL = timeSeriesURL + metrics_name
          
              timeseries_def = {}
              timeseries_def["displayName"] = use_cases[k]["metric-displayname"]
              timeseries_def["types"]=[]
              timeseries_def["types"].append(applications[i]["device-property"]["type"])
              timeseries_def["unit"] = use_cases[k]["unit"] 
              post_param = {'Content-Type':'application/json; charset=utf-8', 'Authorization':'Api-Token {}'.format(tenant_info.tenant_post_token)}
              config_post = requests.put(timeSeriesURL, data = json.dumps(timeseries_def), headers = post_param)
              if config_post.status_code != 200:
                logging.error('postConfigs: failed to create timeseries for %s ', metrics_name)
              else:
                 logging.info('SUCCESS postConfigs status code for {0} '.format(metrics_name))
            #print config_post.text + " " + use_cases[k]["timeseriesId"]
            flag = 1
      
        for j in range(len(use_cases)):
        #for j in range(1):
          json_data = call_http_endpoint(logger, tenant_info, use_cases[j]) 
        
        config_post = send_data_custom_device(logger, restpoint, json_data)
        json_data["series"] = []
        time.sleep(int(data["sleep"]))
        #count = count + 1

  except Exception as e:
    traceback.print_exc()

