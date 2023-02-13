import EntityPage from './entity';

class IntersectionsPage extends EntityPage {
  constructor() {
    super();

    this.elements = {
      ...this.elements,
      intersectionNameLink: (intersectionName) =>
        cy.xpath(`//a[text()="${intersectionName}"]`),
      intersectionTableHref: () =>
        cy.get(
          'table > tbody > tr > td.ant-table-cell > span.intersection > a'
        ),
    };
  }

  createIntersection(intersectionName) {
    this.elements
      .addIntersectionButton()
      .should('be.visible')
      .should('contain.text', '+ Add Intersection')
      .click();
    this.elements.addIntersectionModal().should('be.visible');
    this.elements
      .intersectionModalTitle()
      .should(
        'contain.text',
        'Please enter name and coordinates for new intersection'
      );
    this.elements.enterIntersectionName().type(intersectionName);
    this.elements.enterLatitudeValue().type('34.188057');
    this.elements.enterLongitudeValue().type('84.164458');
    this.elements.submitButton().click();
    cy.wait(15000);
    this.elements.intersectionDeleteButton().should('be.visible');
    this.elements.generalIntersectionInformationTab().should('be.visible');
  }

  deleteIntersection(intersectionName) {
    cy.go('back');
    cy.wait(5000);
    this.elements.addIntersectionButton().should('be.visible');
    this.elements.intersectionTable().should('be.visible');
    this.elements.intersectionTableHref().each(($el) => {
      const value = $el.text();

      if (value === intersectionName) {
        this.elements.intersectionNameLink(intersectionName).click();
        this.elements
          .intersectionDeleteButton()
          .should('be.visible')
          .should('contain.text', 'Delete');
        this.elements.intersectionDeleteButton().click();
        cy.wait(5000);
        this.elements
          .intersectionNameonL2Screen()
          .invoke('val')
          .should('be.empty');
      }
    });
  }

  searchIntersection(intersectionName) {
    this.elements.addIntersectionButton().should('be.visible');
    cy.wait(5000);
    this.elements.intersectionTable().should('be.visible');
    this.elements.intersectionSearch().should('be.visible');
    this.elements
      .intersectionSearchPlaceholderText()
      .should('contain.text', 'Enter Intersection');
    this.elements.intersectionSearch().click();
    this.elements.intersectionSearch().type(`${intersectionName}{enter}`);
    this.elements
      .intersectionTableContents()
      .find('tr')
      .should('have.length', '1');
    this.elements
      .searchedIntersectionName()
      .should('contain.text', `${intersectionName}`);
  }

  deleteSearch(intersectionName) {
    cy.wait(1000);
    this.elements.intersectionSearch().click();
    this.elements.clearIntersectionSearch().click();
    this.elements
      .intersectionSearchPlaceholderText()
      .should('contain.text', 'Enter Intersection');
    this.elements
      .intersectionSearchPlaceholderText()
      .should('not.contain.text', `${intersectionName}`);
  }

  intersectionTable() {
    return cy.xpath('//div[@class="ant-tabs-content-holder"]');
  }
}

export default IntersectionsPage;
