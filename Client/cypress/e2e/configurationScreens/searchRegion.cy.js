import RegionPage from '../../pageObjects/region';

const REGION_NAME = 'CypressTestRegion';

describe('searchRegion', { tags: ['Test', 'Pilot'] }, () => {
  it('SearchRegion', () => {
    const region = new RegionPage();

    // Login
    cy.login(
      Cypress.env('adminSignInUsername'),
      Cypress.env('adminSignInUserPassword')
    );
    cy.title().should('eq', 'GTT Smart Cities');

    // Verify regions search bar
    region.searchBar().should('be.visible').should('contain.text', 'Region:');
    region
      .searchBarPlaceholder()
      .should('have.attr', 'placeholder', 'Please enter');
    region.searchIcon().should('be.visible');
    region.searchBarPlaceholder().type(REGION_NAME);
    region.searchIcon().click();

    // Search Region
    region.searchRegion(REGION_NAME);
    region.regionBreadcrumb().click();

    // Clear region name is search box
    region.searchBarPlaceholder().type(REGION_NAME);
    region.searchIcon().click();
    region.deleteSearch(REGION_NAME);

    // Verify search bar displays placeholder text
    region
      .searchBarPlaceholder()
      .should('have.attr', 'placeholder', 'Please enter');
  });
});
