import React, { Component } from 'react';
import { Form, FormControl } from 'react-bootstrap';
import Button from 'react-bootstrap/Button';
import BootstrapTable from 'react-bootstrap-table-next';
import fetchData from './fetchData';
import { withRouter } from 'react-router-dom';

class AssociateVehicleToAgency extends Component {
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
        this.props.token
      );
      if (response.status === 404) {
        this.setState({
          error: 'Vehicle does not exist',
        });
        return;
      } else if (response.status === 200) {
        const vehicle = await response.json();
        if (vehicle.templateId === 'communicator') {
          this.setState({
            error:
              "Do you want to associate a device? Try 'Associate More Device' below",
          });
          return;
        }
        if (vehicle.groups) {
          const deviceId = vehicle.deviceId;
          const ownedby = vehicle.groups.ownedby[0];
          const agencyName = ownedby.split('/').pop();
          this.setState({
            error: `Vehicle ${deviceId} has already been associated with ${agencyName}`,
          });
          return;
        } else {
          this.setState({
            response: [vehicle].map(vehicle => {
              return {
                deviceId: vehicle.deviceId,
                type: vehicle.attributes.type,
                priority: vehicle.attributes.priority,
                class: vehicle.attributes.class,
                vid: vehicle.attributes.VID,
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
        dataField: 'type',
        text: 'Type',
      },
      {
        dataField: 'priority',
        text: 'Priority',
      },
      {
        dataField: 'class',
        text: 'Class',
      },
      {
        dataField: 'vid',
        text: 'VID',
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
          alert(err.response);
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
              Associate Vehicle
            </Button>
          </div>
        );
      }
    }
    return (
      <div className="AssociateVehicleToAgency">
        <div>
          <h5>Associate More Vehicles</h5>
          <Form inline>
            <FormControl
              type="text"
              placeholder="Search Vehicle Name"
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
export default withRouter(AssociateVehicleToAgency);
