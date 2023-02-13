import RegionPage from '../../pageObjects/region';

describe('sortRegionTable', { tags: ['Test', 'Pilot'] }, () => {
  it('sortRegionName', () => {
    const region = new RegionPage();

    // Login
    cy.login(
      Cypress.env('adminSignInUsername'),
      Cypress.env('adminSignInUserPassword')
    );
    cy.title().should('eq', 'GTT Smart Cities');

    // Verify Regions table is visible and sorted in ascending order by default
    region.regionTable().should('be.visible');
    region.regionTableTitle().should('contain.text', 'Region');
    region.regionNameAscending().should('have.class', 'active');

    for (let i = 1; i <= 20; i++) {
      const xpathVal = `//tbody[@class="ant-table-tbody"]//tr[${i}]//td[2]`;

      let oldRegionName = '0';

      cy.xpath(xpathVal).each(($el) => {
        const rowVal = $el.text();
        const newRegionName = rowVal;
        expect(oldRegionName.localeCompare(newRegionName)).to.be.equal(-1);
        oldRegionName = newRegionName;
      });
    }

    // Verify Regions table is sorted in descending order
    region.regionTableName().click();
    region.regionNameDescending().should('have.class', 'active');

    for (let i = 1; i <= 20; i++) {
      const xpathVal = `//tbody[@class="ant-table-tbody"]//tr[${i}]//td[2]`;

      let oldRegionName = '0';

      cy.xpath(xpathVal).each(($el) => {
        const rowVal = $el.text();
        const newRegionName = rowVal;
        expect(oldRegionName.localeCompare(newRegionName)).to.be.equal(-1);
        oldRegionName = newRegionName;
      });
    }
  });
});
