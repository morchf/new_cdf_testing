import React, { Component } from 'react';
import './App.css';
import fetchData from './fetchData';
import CustomerPage from './customerPage';
import ServerPage from './serverPage';
import SearchBar from './SearchBar';

class App extends Component {
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

  componentDidMount() {
    this.fetchVPSS();
  }

  fetchVPSS = async () => {
    this.setState({
      vpss: 'initial',
    });

    try {
      // load data
      const fetchedData = await fetchData();
      this.setState({ vpss: fetchedData });
    } catch (error) {
      this.setState({ error: true });
    }
  };

  receiveCustomerName(newCustomerName) {
    this.setState({
      search: newCustomerName.customerName,
      visible: newCustomerName.visible,
    });
  }

  render() {
    const items = this.state;
    const customerNames = Array.from(new Set(items.vpss.map(x => x.customerName)))

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

export default App;
