from bs4 import BeautifulSoup
import json
import random
import datetime
import calendar
import time
import os
from operator import itemgetter, attrgetter

import urllib

import boto.s3
from boto.s3.connection import S3Connection

import filesystem as fslib
import simpleDB as dblib

"""
Article data provider
From article XML, get some data for use in workflows and templates
"""

class article(object):
  
  def __init__(self, settings = None, tmp_dir = None):
    self.settings = settings
    self.tmp_dir = tmp_dir
    
    # Default tmp_dir if not specified
    self.tmp_dir_default = "article_provider"
    
    # SimpleDB connection for looking up S3 keys
    self.db = None
    if(self.settings is not None):
      # Data provider
      self.db = dblib.SimpleDB(settings)
    
    # S3 connection
    self.s3_conn = None
    
    # Filesystem provider
    self.fs = None
    
    # Default S3 bucket name
    self.bucket_name = None
    if(self.settings is not None):
      self.bucket_name = self.settings.bucket
    
    # Some defaults
    self.article_data = None
        
  def connect(self):
    """
    Connect to S3 using the settings
    """
    s3_conn = S3Connection(self.settings.aws_access_key_id, self.settings.aws_secret_access_key)
    self.s3_conn = s3_conn
    return self.s3_conn

  def get_bucket(self, bucket_name = None):
    """
    Using the S3 connection, lookup the bucket
    """
    if(self.s3_conn is None):
      s3_conn = self.connect()
    else:
      s3_conn = self.s3_conn
    
    if(bucket_name is None):
      # Use the object bucket_name if not provided
      bucket_name = self.bucket_name
    
    # Lookup the bucket
    bucket = s3_conn.lookup(bucket_name)

    return bucket

  def get_s3key(self, s3_key_name, bucket = None):
    """
    Get the S3 key from the bucket
    If the bucket is not provided, use the object bucket
    """
    if(bucket is None):
      bucket = self.get_bucket()
    
    s3key = bucket.get_key(s3_key_name)
    
    return s3key

  def parse_article_file(self, document, filename = None):
    """
    Given a filename to an article file, download
    or copy it using the filesystem provider,
    then parse it
    """

    if(self.fs is None):
      self.fs = self.get_fs()
    
    # Save the document to the tmp_dir
    self.fs.write_document_to_tmp_dir(document, filename)

    parsed = self.parse_article_xml(self.fs.document)
    
    return parsed

  def parse_article_xml(self, document):
    """
    Given article XML, parse
    it and return an object representation
    """
    
    try:
      soup = self.parse_document(document)
      self.doi = self.parse_doi(soup)
      if(self.doi):
        self.doi_id = self.get_doi_id(self.doi)
        self.doi_url = self.get_doi_url(self.doi)
        self.lens_url = self.get_lens_url(self.doi)
        self.tweet_url = self.get_tweet_url(self.doi)
  
      self.pub_date = self.parse_pub_date(soup)
      if(self.pub_date):
        self.pub_date_timestamp = self.get_pub_date_timestamp(self.pub_date)
      
      self.article_title = self.parse_article_title(soup)
      
      return True
    except:
      return False
  
  def get_article_data(self, doi_id = None, document = None):
    """
    Return the article data for use in templates
    """
    
    filename = None
    # Check for the document
    if(document is None):
      # No document? Find it on S3, save the content to
      #  the tmp_dir
      if(self.fs is None):
        self.fs = self.get_fs()
      # Connect to SimpleDB and get the latest article XML S3 object name
      self.db.connect()
      # Look up the latest XMl file by doi_id, should return a list of 1
      log_item = self.db.elife_get_article_S3_file_items(file_data_type = "xml", doi_id = doi_id, latest = True)
      s3_key_name = None
      
      try:
        s3_key_name = log_item[0]["name"]
      except IndexError:
        return False

      s3_key = self.get_s3key(s3_key_name)
      contents = s3_key.get_contents_as_string()
      
      # Get the filename from the s3_key_name
      try:
        path_array = s3_key_name.split('/')
        filename = path_array[-1]
      except:
        filename = "s3_article.zip"

      self.fs.write_content_to_document(content = contents, filename = filename, mode = "wb")
      document = self.fs.get_document()
    else:
      # Write it with the filesystem provider
      self.fs.write_document_to_tmp_dir(document)
    
    # Make a copy_of the filename, to retain the file extension of the original, but not have a file overwrite itself
    filename = "copy_of_" + self.fs.get_document()
    document = self.fs.get_tmp_dir() + os.sep + self.fs.get_document()
    
    # Parse the file
    parsed = self.parse_article_file(document, filename)
    return parsed
    
  def get_fs(self):
    """
    For running tests, return the filesystem provider
    so it can be interrogated
    """
    if(self.fs is None):
      # Create the filesystem provider
      self.fs = fslib.Filesystem(self.get_tmp_dir())
    return self.fs
  
  def get_tmp_dir(self):
    """
    Get the temporary file directory, but if not set
    then make the directory
    """
    if(self.tmp_dir):
      return self.tmp_dir
    else:
      self.tmp_dir = self.tmp_dir_default
      
    return self.tmp_dir
    
    
  def get_tweet_url(self, doi):
    """
    Given a DOI, return a tweet URL
    """
    doi_url = self.get_doi_url(doi)
    f = {"text": doi_url}
    tweet_url ="http://twitter.com/intent/tweet?" + urllib.urlencode(f)
    return tweet_url
    
  def get_doi_url(self, doi):
    """
    Given a DOI, get the URL for the DOI
    """
    doi_url ="http://dx.doi.org/" + doi
    return doi_url
    
  def get_lens_url(self, doi):
    """
    Given a DOI, get the URL for the lens article
    """
    doi_id = self.get_doi_id(doi)
    lens_url = "http://lens.elifesciences.org/" + doi_id
    return lens_url
    
  def get_doi_id(self, doi):
    """
    Given a DOI, return the doi_id part of it
    e.g. DOI 10.7554/eLife.00013
    split on dot and the last list element is doi_id
    """
    x = doi.split(".")
    doi_id = x[-1]
    return doi_id
  
  def get_pub_date_timestamp(self, pub_date):
    """
    Given a time struct for a publish date
    parse and return a timestamp for it
    """
    timestamp = None
    try:
      timestamp = calendar.timegm(pub_date)
    except(TypeError):
      # Date did not convert
      pass
    return timestamp
    
  """
  Some quick copy and paste from elife-api-prototype parseNLM.py parser to get the basics for now
  """
  
  def parse_document(self, document):
    return self.parse_xml(self.fs.read_document_from_tmp_dir(document))
  
  def parse_xml(self, xml):
    soup = BeautifulSoup(xml, "lxml")
    return soup
  
  def parse_doi(self, soup):
    doi = None
    doi_tags = self.extract_nodes(soup, "article-id", attr = "pub-id-type", value = "doi")
    for tag in doi_tags:
      # Only look at the doi tag directly inside the article-meta section
      if (tag.parent.name == "article-meta"):
        doi = tag.text
    return doi
  
  def parse_pub_date(self, soup, pub_type = "ppub"):
    """
    Find the publishing date for populating
    pub_date_date, pub_date_day, pub_date_month, pub_date_year, pub_date_timestamp
    Default pub_type is ppub, but will revert to epub if tag is not found
    """
    tz = "UTC"
    
    try:
      pub_date_section = self.extract_nodes(soup, "pub-date", attr = "pub-type", value = pub_type)
      if(len(pub_date_section) == 0):
        if(pub_type == "ppub"):
          pub_type = "epub"
        pub_date_section = self.extract_nodes(soup, "pub-date", attr = "pub-type", value = pub_type)
      (day, month, year) = self.get_ymd(pub_date_section[0])
  
    except(IndexError):
      # Tag not found, try the other
      return None
    
    date_string = None
    try:
      date_string = time.strptime(year + "-" + month + "-" + day + " " + tz, "%Y-%m-%d %Z")
    except(TypeError):
      # Date did not convert
      pass
  
    return date_string
    
  def parse_article_title(self, soup):
    title_text = self.extract_node_text(soup, "article-title")
    return title_text
    
  def extract_first_node(self, soup, nodename):
    tags = self.extract_nodes(soup, nodename)
    try:
      tag = tags[0]
    except(IndexError):
      # Tag not found
      return None
    return tag
    
  def extract_nodes(self, soup, nodename, attr = None, value = None):
    tags = soup.find_all(nodename)
    if(attr != None and value != None):
      # Further refine nodes by attributes
      tags_by_value = []
      for tag in tags:
        try:
          if tag[attr] == value:
            tags_by_value.append(tag)
        except KeyError:
          continue
      return tags_by_value
    return tags
  
  def extract_node_text(self, soup, nodename, attr = None, value = None):
    """
    Extract node text by nodename, unless attr is supplied
    If attr and value is specified, find all the nodes and search
      by attr and value for the first node
    """
    tag_text = None
    if(attr == None):
      tag = self.extract_first_node(soup, nodename)
      try:
        tag_text = tag.text
      except(AttributeError):
        # Tag text not found
        return None
    else:
      tags = self.extract_nodes(soup, nodename, attr, value)
      for tag in tags:
        try:
          if tag[attr] == value:
            tag_text = tag.text
        except KeyError:
          continue
    return tag_text
  
  def get_ymd(self, soup):
    """
    Get the year, month and day from child tags
    """
    day = self.extract_node_text(soup, "day")
    month = self.extract_node_text(soup, "month")
    year = self.extract_node_text(soup, "year")
    return (day, month, year)
      