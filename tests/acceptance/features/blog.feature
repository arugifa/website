Feature: Blog

Scenario: Navigate to blog articles
    Given I wrote 3 blog articles
    When I access to my website
    Then I should see all articles
    And they should be sorted chronologically in descending order

Scenario: Read a blog article
    Given I wrote 1 blog article
    When I access to my website
    And I go to my article
    Then I should see its content
