import RegionPage from '../../pageObjects/region';
import AgencyPage from '../../pageObjects/agency';

const REGION_NAME = 'CypressTestRegion';

describe('searchAgency', { tags: ['Test', 'Pilot'] }, () => {
  it('SearchAgency', () => {
    const region = new RegionPage();
    const agency = new AgencyPage();

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

    // Verify Agency name is in ascending order by default
    agency.agencyNameAscending().should('have.class', 'active');

    for (let i = 1; i <= 3; i++) {
      const xpathVal = `(//tbody[@class="ant-table-tbody"])[2]//tr[${i}]/td[2]`;

      let oldRegionName = '0';

      cy.xpath(xpathVal).each(($el) => {
        const rowVal = $el.text();
        const newRegionName = rowVal;
        if (rowVal != null)
          expect(oldRegionName.localeCompare(newRegionName)).to.be.equal(-1);
        oldRegionName = newRegionName;
      });
    }

    // Verify Agency city is sorted in ascending order
    agency.agencyCity().click();
    agency.agencyCityAscending().should('have.class', 'active');

    for (let i = 1; i <= 3; i++) {
      const xpathVal = `(//tbody[@class="ant-table-tbody"])[2]//tr[${i}]/td[4]`;

      let oldRegionName = '0';

      cy.xpath(xpathVal).each(($el) => {
        const rowVal = $el.text();
        const newRegionName = rowVal;
        if (rowVal != null)
          expect(oldRegionName.localeCompare(newRegionName)).to.be.equal(-1);
        oldRegionName = newRegionName;
      });
    }

    // Verify Agency state is sorted in descending order
    agency.agencyState().dblclick();
    agency.agencyStateDescending().should('have.class', 'active');

    for (let i = 1; i <= 3; i++) {
      const xpathVal = `(//tbody[@class="ant-table-tbody"])[2]//tr[${i}]/td[5]`;

      let oldRegionName = '0';

      cy.xpath(xpathVal).each(($el) => {
        const rowVal = $el.text();
        const newRegionName = rowVal;
        if (rowVal != null)
          expect(oldRegionName.localeCompare(newRegionName)).to.be.equal(-1);
        oldRegionName = newRegionName;
      });
    }
  });
});
