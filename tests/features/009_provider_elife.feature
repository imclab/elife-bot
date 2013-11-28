Feature: Use elife provider
  In order to use elife as a provider
  As a worker
  I want to read elife object attributes
  
  Scenario: Instantiate an elife provider and read attributes
    Given I create an elife provider
    When I get a value from the elife provider for the attribute <attribute>
    Then I have the value <value>

  Examples:
    | attribute      | value    
    | facebook_url   | http://www.facebook.com/elifesciences        
    | submit_url     | http://submit.elifesciences.org/
