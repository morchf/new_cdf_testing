import RegionPage from '../../pageObjects/region';
import AgencyPage from '../../pageObjects/agency';
import IntersectionPage from '../../pageObjects/intersection';

const REGION_NAME = 'CypressTestRegion';
const AGENCY_NAME = 'CypressTestAgency';
const INTERSECTION_NAME = 'Cypress Automation Test Search';

describe('createIntersection', { tags: ['Test', 'Pilot'] }, () => {
  it('Intersection', () => {
    const region = new RegionPage();
    const agency = new AgencyPage();
    const intersection = new IntersectionPage();

    // Login
    cy.login(
      Cypress.env('adminSignInUsername'),
      Cypress.env('adminSignInUserPassword')
    );
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

    // Verify agency search bar
    region.searchBar().should('be.visible').should('contain.text', 'Agency:');
    region
      .searchBarPlaceholder()
      .should('have.attr', 'placeholder', 'Please enter');
    region.searchIcon().should('be.visible');
    region.searchBarPlaceholder().type(AGENCY_NAME);
    region.searchIcon().click();

    // Search Agency
    agency.searchAgency(AGENCY_NAME);

    // Navigate to intersection page (Using URL value until intersection button is present on sidemenu)
    cy.visit(Cypress.env('intersectionUrl'));
    intersection.intersectionTable().should('be.visible');

    // Search Intersection
    intersection.searchIntersection(INTERSECTION_NAME);

    // Clear Intersection Search
    intersection.deleteSearch(INTERSECTION_NAME);
  });
});
