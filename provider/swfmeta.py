import json
import random
import datetime
import calendar
import time

import boto.swf

"""
SWFMeta data provider
Functions to provide meta data from SWF so code is not duplicated
"""

class SWFMeta(object):
  
  def __init__(self, settings):
    self.settings = settings
    
    self.conn = None
    
    # Workflow execution history info
    self.infos = None
    
    # Workflow execution count
    self.count = None
    
  def connect(self):
    # Simple connect
    self.conn = boto.swf.layer1.Layer1(self.settings.aws_access_key_id, self.settings.aws_secret_access_key)
    return self.conn
  
  def get_closed_workflow_execution_count(self, domain = None, workflow_id = None, workflow_name = None, workflow_version = None, start_oldest_date = None, start_latest_date = None, close_status = None):
    """
    Get the count of executions from SWF, limited to 90 days by Amazon,
    for the criteria supplied
    Relies on boto.swf.count_closed_workflow_executions
    Note: Cannot send a workflow_name and close_status at the same time
    """
    if(self.conn is None):
      self.connect()
      
    if(domain is None):
      domain = self.settings.domain
      
    # Still need to handle the nextPageToken
    count = self.conn.count_closed_workflow_executions(
      domain            = domain,
      workflow_id       = workflow_id,
      workflow_name     = workflow_name,
      workflow_version  = workflow_version,
      start_oldest_date = start_oldest_date,
      start_latest_date = start_latest_date,
      close_status      = close_status)

    self.count = count
    return count

  def get_closed_workflow_executionInfos(self, domain = None, workflow_id = None, workflow_name = None, workflow_version = None, start_oldest_date = None, start_latest_date = None, close_status = None, maximum_page_size = 100):
    """
    Get the full history of executions from SWF, limited to 90 days by Amazon,
    for the criteria supplied
    Relies on boto.swf.list_closed_workflow_executions with some wrappers and
    handling of the nextPageToken if encountered
    """
    if(self.conn is None):
      self.connect()
      
    if(domain is None):
      domain = self.settings.domain
      
    # Cannot send a workflow_name and close_status at the same time to handle it
    #   {u'message': u'Cannot specify more than one exclusive filters in the same query: [WorkflowTypeFilter, CloseStatusFilter]
    #   ', u'__type': u'com.amazon.coral.validate#ValidationException'}
    if((workflow_name is not None or workflow_id is not None) and close_status is not None):
      close_status_to_query = None
    else:
      close_status_to_query = close_status
    
    # Still need to handle the nextPageToken
    infos = self.conn.list_closed_workflow_executions(
      domain            = domain,
      workflow_id       = workflow_id,
      workflow_name     = workflow_name,
      workflow_version  = workflow_version,
      start_oldest_date = start_oldest_date,
      start_latest_date = start_latest_date,
      close_status      = close_status_to_query,
      maximum_page_size = maximum_page_size)

    # Check if there is no nextPageToken, if there is none
    #  return the result, nothing to page
    next_page_token = None
    try:
      next_page_token = infos["nextPageToken"]
    except KeyError:
      next_page_token = None

    # Continue, we have a nextPageToken. Assemble a full array of events by continually polling
    if(next_page_token is not None):
      all_infos = infos["executionInfos"]
      while(next_page_token is not None):
        try:
          next_page_token = infos["nextPageToken"]
          if(next_page_token is not None):
            infos = self.conn.list_closed_workflow_executions(
              domain            = domain,
              workflow_id       = workflow_id,
              workflow_name     = workflow_name,
              workflow_version  = workflow_version,
              start_oldest_date = start_oldest_date,
              start_latest_date = start_latest_date,
              close_status      = close_status_to_query,
              maximum_page_size = maximum_page_size,
              next_page_token   = next_page_token)
            
            for execution in infos["executionInfos"]:
              all_infos.append(execution)
        except KeyError:
          next_page_token = None
      
      # Finally, reset the original decision response with the full set of events
      infos["executionInfos"] = all_infos

    # Handle if a close_status was supplied as well as a workflow_name
    if(workflow_name is not None and close_status is not None):
      good_infos = []
      for execution in infos["executionInfos"]:
        if execution["closeStatus"] == close_status:
          good_infos.append(execution)
      infos["executionInfos"] = good_infos

    self.infos = infos
    return infos

  def get_last_completed_workflow_execution_startTimestamp(self, domain = None, workflow_id = None, workflow_name = None, workflow_version = None):
    """
    For the specified workflow_id, or workflow_name + workflow_version,
    get the startTimestamp for the last successfully completed workflow
    execution
    Use the full 90 days of execution history provided by Amazon
    """
    
    latest_startTimestamp = None
    
    start_latest_date = calendar.timegm(time.gmtime())
    start_oldest_date = start_latest_date - (60*60*24*90)
    close_status = "COMPLETED"

    infos = self.get_closed_workflow_executionInfos(
      domain            = domain,
      workflow_id       = workflow_id,
      workflow_name     = workflow_name,
      workflow_version  = workflow_version,
      start_latest_date = start_latest_date,
      start_oldest_date = start_oldest_date,
      close_status      = close_status)
    
    # Find the latest run
    for execution in infos["executionInfos"]:
      if(latest_startTimestamp is None):
        latest_startTimestamp = execution['startTimestamp']
        continue
      if(execution['startTimestamp'] > latest_startTimestamp):
        latest_startTimestamp = execution['startTimestamp']
    
    return latest_startTimestamp
