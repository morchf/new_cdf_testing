import React, { Component } from 'react';
import './App.css';
import fetchData from './fetchData';
import CustomerPage from './customerPage';
import ServerPage from './serverPage';
import SearchBar from './SearchBar';
import { withRouter } from 'react-router-dom';

class VPSPage extends Component {
  constructor(props) {
    super(props);
    this.state = {
      vpss: [],
      search: '',
      visible: true,
      error: false,
    };
    this.receiveCustomerName = this.receiveCustomerName.bind(this);
  }

  async componentDidMount() {
    try {
      // load data
      const fetchedData = await fetchData('DALLAS');
      this.setState({ vpss: fetchedData });
    } catch (error) {
      this.setState({ error: error });
    }
  }

  receiveCustomerName(newCustomerName) {
    this.setState({
      search: newCustomerName.customerName,
      visible: newCustomerName.visible,
    });
  }

  render() {
    const items = this.state;
    const customerNames = [
      ...new Set(Array.from(items.vpss).map(x => x.customerName)),
    ];

    return (
      <div className="App" style={{ height: '100vh' }}>
        {items.visible ? (
          <div>
            <SearchBar
              receiveCustomerName={this.receiveCustomerName}
              customerNames={customerNames}
            />
            <CustomerPage vpss={items.vpss} />
          </div>
        ) : (
          <ServerPage vpss={items.vpss} customerName={items.search} />
        )}
      </div>
    );
  }
}

export default withRouter(VPSPage);
