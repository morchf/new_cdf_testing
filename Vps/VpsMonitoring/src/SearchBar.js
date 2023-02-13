import React, { Component } from 'react';

class SearchBar extends Component {
  constructor(props) {
    super(props);
    this.state = { customerName: '', visible: true };
    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(evt) {
    this.setState({ customerName: evt.target.value });
  }

  handleSubmit(evt) {
    this.props.receiveCustomerName(this.state);
    this.setState = { customerName: '' };
  }

  render() {
    return (
      <div>
        <form onSubmit={this.handleSubmit}>
          <input
            id="customerName"
            type="text"
            placeholder="search for a customer"
            value={this.state.customerName}
            onChange={this.handleChange}
          />
          <button
            onClick={() => {
              if (this.props.customerNames.includes(this.state.customerName)) {
                this.setState({ visible: false });
              } else {
                this.setState({ customerName: '' });
              }
            }}
          >
            Change
          </button>
        </form>
      </div>
    );
  }
}
export default SearchBar;
