import boto.swf
import json
import random
import datetime
import calendar
import time
import requests
import os

import activity

import boto.s3
from boto.s3.connection import S3Connection

import provider.filesystem as fslib
import provider.templates as templatelib
import provider.article as articlelib

"""
LensArticle activity
"""

class activity_LensArticle(activity.activity):
	
	def __init__(self, settings, logger, conn = None, token = None, activity_task = None):
		activity.activity.__init__(self, settings, logger, conn, token, activity_task)

		self.name = "LensArticle"
		self.version = "1"
		self.default_task_heartbeat_timeout = 30
		self.default_task_schedule_to_close_timeout = 60*5
		self.default_task_schedule_to_start_timeout = 30
		self.default_task_start_to_close_timeout= 60*5
		self.description = "Create a lens article index.html page for the particular article."
		
		# Create the filesystem provider
		self.fs = fslib.Filesystem(self.get_tmp_dir())
		
		# Templates provider
		self.templates = templatelib.Templates(settings, self.get_tmp_dir())
		
		# article data provider
		self.article = articlelib.article(settings, self.get_tmp_dir())
		
		# Default templates directory
		self.from_dir = "template"

	def do_activity(self, data = None):
		"""
		Do the work
		"""
		if(self.logger):
			self.logger.info('data: %s' % json.dumps(data, sort_keys=True, indent=4))
		
		elife_id = data["data"]["elife_id"]
		
		xml_file_url = self.get_xml_file_url(elife_id)
		article = self.article.get_article_data(doi_id = elife_id)
		
		lens_article_s3key = self.get_lens_article_s3key(elife_id)
		
		filename = "index.html"
		
		article_html = self.get_article_html(xml_file_url = xml_file_url, article = self.article)
		
		# Write the document to disk first
		self.fs.write_content_to_document(article_html, filename)
		
		# Now, set the S3 object to the contents of the filename
		# Connect to S3
		s3_conn = S3Connection(self.settings.aws_access_key_id, self.settings.aws_secret_access_key)
		# Lookup bucket
		bucket_name = self.settings.lens_bucket
		bucket = s3_conn.lookup(bucket_name)
		s3key = boto.s3.key.Key(bucket)
		s3key.key = lens_article_s3key
		s3key.set_contents_from_filename(self.get_document(), replace=True)
		
		if(self.logger):
			self.logger.info('LensArticle created for: %s' % lens_article_s3key)

		return True
	
	def get_xml_file_url(self, elife_id):
		"""
		Given an eLife article DOI ID (5 digits) assemble the
		URL of where it is found
		"""
		xml_url = "https://s3.amazonaws.com/" + self.settings.cdn_bucket + "/elife-articles/" + elife_id + "/elife" + elife_id + ".xml"
		
		return xml_url
	
	def get_lens_article_s3key(self, elife_id):
		"""
		Given an eLife article DOI ID (5 digits) assemble the
		S3 key name for where to save the article index.html page
		"""
		lens_article_s3key = "/" + elife_id + "/index.html"
		
		return lens_article_s3key
		
	def get_article_html(self, xml_file_url, article = None, from_dir = None):
		"""
		Given the URL of the article XML file, create a lens article index.html page
		using header, footer or template, as required
		"""
		article_html = None
		if(from_dir is None):
			from_dir = self.from_dir
		warmed = self.warm_templates(from_dir)
		if(warmed is True):
			article_html = self.templates.get_lens_article_html(from_dir, xml_file_url, article)
			
		return article_html
		
	def warm_templates(self, from_dir):
		# Prepare templates
		self.templates.copy_lens_templates(from_dir)
		if(self.templates.lens_templates_warmed is not True):
			if(self.logger):
				self.logger.info('LensArticle email templates did not warm successfully')
			# Stop now! Return False if we do not have the necessary files
			return False
		else:
			if(self.logger):
				self.logger.info('LensArticle email templates warmed')
			return True
		return None
		
	def get_document(self):
		"""
		Exposed for running tests
		"""
		if(self.fs.tmp_dir):
			full_filename = self.fs.tmp_dir + os.sep + self.fs.get_document()
		else:
			full_filename = self.fs.get_document()
		
		return full_filename
