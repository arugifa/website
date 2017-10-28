Feature: Recommended Material

Scenario: Navigate to recommended material
    Given I read and recommend 3 articles
    When I access to my website
    And I go to my recommended material
    Then I should see 3 recommended articles
    And they should be sorted chronologically in descending order
