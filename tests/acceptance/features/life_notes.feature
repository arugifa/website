Feature: Life Notes

Scenario: Navigate to life notes
    Given I wrote 3 life notes
    When I access to my website
    And I go to my life notes
    Then I should see 3 life notes
    And they should be sorted chronologically in descending order
