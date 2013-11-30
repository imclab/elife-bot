Feature: Use Templates provider
  In order to use Templates as a provider
  As a worker
  I want to add template files from local block storage
  
  Scenario: Save a template file using the templates provider
    Given I have a tmp_base_dir <tmp_base_dir>
    And I have test name <test_name>
    And I get the current datetime
    And I get the tmp_dir from the world
    And I create a templates provider
    And I have a document <document>
    And I have the template name <template_name>
    And I get a filesystem provider from the templates provider
    When I read the document to content
    And I save template contents to tmp dir with templates provider
    And I get the filesystem document
    Then I have the world filesystem document <filesystem_document>

  Examples:
    | tmp_base_dir  | test_name     | document                              | template_name     | filesystem_document 
    | tmp           | tmpl_provider | test_data/templates/email_header.html | email_header.html | email_header.html 

  Scenario: Render email templates using the templates provider
    Given I have a tmp_base_dir <tmp_base_dir>
    And I have test name <test_name>
    And I get the current datetime
    And I get the tmp_dir from the world
    And I create a templates provider
    And I have a base directory <base_dir>
    And I have the author json <author_json>
    And I have the article json <article_json>
    And I have the elife json <elife_json>
    And I get email templates list from the template provider
    And I get a filesystem provider from the templates provider
    When I read each base dir plus templates list document to content
    And I set the templates provider email templates warmed to True
    And I get author publication email body from the templates provider
    Then I have the email body <email_body>

  Examples:
    | tmp_base_dir  | test_name     | base_dir             | author_json          | article_json                   | elife_json                            | email_body
    | tmp           | tmpl_provider | test_data/templates/ | {"first_nm": "Test"} | {"doi_url": "http://doi.org/"} | {"submit_url": "http://example.com/"} | Header\n<p>Dear Test, <a href="http://doi.org/">read it</a> online, <a href="http://example.com/">submit</a> your best work to eLife too.</p>\nFooter
    
  Scenario: Render email templates using the templates provider, elife and article objects
    Given I have imported a settings module
    And I have the settings environment <env>
    And I get the settings
    And I have a tmp_base_dir <tmp_base_dir>
    And I have test name <test_name>
    And I get the current datetime
    And I get the tmp_dir from the world
    And I create a templates provider
    And I have a base directory <base_dir>
    And I have the author json <author_json>
    And I create an elife provider
    And I create an article provider
    And I have the document name <document_name>
    And I parse the document with the article provider
    And I get email templates list from the template provider
    And I get a filesystem provider from the templates provider
    When I read each base dir plus templates list document to content
    And I set the templates provider email templates warmed to True
    And I get author publication email body from the templates provider
    Then I have the email body <email_body>
  
  Examples:
    | env | tmp_base_dir  | test_name     | base_dir             | author_json          | document_name	           | email_body
    | dev | tmp           | tmpl_provider | test_data/templates/ | {"first_nm": "Test"} | test_data/elife00013.xml | Header\n<p>Dear Test, <a href="http://dx.doi.org/10.7554/eLife.00013">read it</a> online, <a href="http://submit.elifesciences.org/">submit</a> your best work to eLife too.</p>\nFooter
    
  Scenario: Render lens article template using the templates provider
    Given I have imported a settings module
    And I have the settings environment <env>
    And I get the settings
    And I have a tmp_base_dir <tmp_base_dir>
    And I have test name <test_name>
    And I get the current datetime
    And I get the tmp_dir from the world
    And I create a templates provider
    And I have a from directory <from_dir>
    And I create an article provider
    And I have the document name <document_name>
    And I have the xml file url <xml_file_url>
    And I parse the document with the article provider
    When I copy lens templates using the templates provider
    And I get lens article html from the templates provider
    Then I have the article html <article_html>
    
  Examples:
    | env | tmp_base_dir  | test_name     | from_dir             | document_name	          | xml_file_url                      | article_html
    | dev | tmp           | tmpl_provider | test_data/templates  | test_data/elife00013.xml | http://example.com/elife00013.xml | <!DOCTYPE html>\n<html xmlns:mml="http://www.w3.org/1998/Math/MathML">\n<head>\n<title>A bacterial sulfonolipid triggers multicellular development in the closest living relatives of animals \| eLife Lens</title>\n<script>\ndocument_url: "http://example.com/elife00013.xml"\n</script>\n</head>\n<body>\n</body>\n</html>
    