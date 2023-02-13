import React, { Component } from 'react';
import { Form, FormControl } from 'react-bootstrap';
import Button from 'react-bootstrap/Button';
import BootstrapTable from 'react-bootstrap-table-next';
import fetchData from './fetchData';
import { withRouter } from 'react-router-dom';

class AssociateDeviceToAgency extends Component {
  constructor(props) {
    super(props);
    this.state = {
      response: '',
      error: '',
      searchInput: '',
      selected: [],
    };
    this.handleAssociateState = this.handleAssociateState.bind(this);
  }

  searchHandler = event => {
    this.setState({
      searchInput: event.target.value,
    });
  };
  searchSubmitHandler = async event => {
    const token = this.props.token;
    try {
      event.preventDefault();
      const searchInput = this.state.searchInput.toLowerCase();
      if (searchInput === '') {
        this.setState({
          error: 'No input',
        });
      }
      const response = await fetchData(
        '/devices/' + searchInput,
        'GET',
        null,
        '',
        token
      );
      if (response.status === 404) {
        this.setState({
          error: 'Device does not exist',
        });
        return;
      } else if (response.status === 200) {
        const device = await response.json();
        if (device.templateId !== 'communicator') {
          this.setState({
            error:
              "Do you want to associate a vehicle? Try 'Associate More Vehicle' Above",
          });
          return;
        }
        if (device.groups) {
          const deviceId = device.deviceId;
          const ownedby = device.groups.ownedby[0];
          const agencyName = ownedby.split('/').pop();
          this.setState({
            error: `Device ${deviceId} has already been associated with ${agencyName}`,
          });
          return;
        } else {
          this.setState({
            response: [device].map(device => {
              return {
                deviceId: device.deviceId,
                uniqueId: device.attributes.uniqueId,
                IMEI: device.attributes.IMEI,
                addressLAN: device.attributes.addressLAN,
                addressWAN: device.attributes.addressWAN,
                addressMAC: device.attributes.addressMAC,
                gttSerial: device.attributes.gttSerial,
                model: device.attributes.model,
                make: device.attributes.make,
              };
            }),
            selected: [],
          });
        }
      } else {
        this.setState({
          error: `${response.status} : Internal error'}`,
        });
      }
    } catch (err) {
      this.setState({
        error: err,
      });
      alert(err.response);
    }
  };
  handleOnSelect = (row, isSelect) => {
    if (isSelect) {
      this.setState(() => ({
        selected: [...this.state.selected, row.deviceId],
      }));
    } else {
      this.setState(() => ({
        selected: this.state.selected.filter(x => x !== row.deviceId),
      }));
    }
  };
  handleAssociateState() {
    this.setState({ response: '', error: '', searchInput: '', selected: [] });
  }
  render() {
    const columns = [
      {
        dataField: 'deviceId',
        text: 'Device ID',
      },
      {
        dataField: 'IMEI',
        text: 'IMEI',
      },
      {
        dataField: 'addressLAN',
        text: 'LAN Address',
      },
      {
        dataField: 'addressWAN',
        text: 'WAN Address',
      },
      {
        dataField: 'addressMAC',
        text: 'MAC Address',
      },
      {
        dataField: 'gttSerial',
        text: 'GTT Serial',
      },
      {
        dataField: 'model',
        text: 'Model',
      },
      {
        dataField: 'make',
        text: 'Make',
      },
    ];

    const selectRow = {
      mode: 'checkbox',
      clickToSelect: true,
      selected: this.state.selected,
      onSelect: this.handleOnSelect,
    };

    function DeviceTable({
      items,
      error,
      selected,
      agencyGroupPath,
      token,
      onResponseChange,
      handleAssociateState,
    }) {
      const groupPath = agencyGroupPath.replace(/\//g, '%2f');
      const handleClick = async e => {
        try {
          e.preventDefault();
          const url = `/devices/${selected}/ownedby/groups/${groupPath}`;
          const response = await fetchData(url, 'PUT', null, pubkey, privkey, '', token);
          if (response.status === 204) {
            onResponseChange(response.status);
            alert('Success');
            handleAssociateState();
          } else {
            alert(response);
          }
        } catch (err) {
          console.log(err);
          alert(err);
        }
      };
      if (error) {
        return <p>{error}</p>;
      }
      if (!items || items.length === 0) {
        return '';
      } else {
        return (
          <div className="SearchTable">
            <BootstrapTable
              keyField="deviceId"
              data={items}
              columns={columns}
              noDataIndication={'No results found'}
              selectRow={selectRow}
            />
            <Button
              className="float-right"
              variant="outline-primary"
              onClick={handleClick}
            >
              Associate Device
            </Button>
          </div>
        );
      }
    }
    return (
      <div className="AssociateDeviceToAgency">
        <div>
          <h5>Associate More Devices</h5>
          <Form inline>
            <FormControl
              type="text"
              placeholder="Search Device Name"
              value={this.state.searchInput}
              className="mr-sm-2"
              onChange={this.searchHandler}
            />
            <Button
              variant="outline-success"
              type="submit"
              onClick={this.searchSubmitHandler}
            >
              Search
            </Button>
          </Form>

          <DeviceTable
            items={this.state.response}
            error={this.state.error}
            selected={this.state.selected}
            agencyGroupPath={this.props.agencyGroupPath}
            token={this.props.token}
            onResponseChange={this.props.onResponseChange}
            handleAssociateState={this.handleAssociateState}
          />
        </div>
      </div>
    );
  }
}
export default withRouter(AssociateDeviceToAgency);
