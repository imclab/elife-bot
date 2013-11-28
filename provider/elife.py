"""
eLife data provider
Get eLife data for template rendering
"""

class elife(object):
  
  def __init__(self, settings = None):
    self.settings = settings

    # Defaults
    self.facebook_url = "http://www.facebook.com/elifesciences"
    self.submit_url = "http://submit.elifesciences.org/"
