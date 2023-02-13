import React, { Component } from 'react';
import { nest, sum } from 'd3';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';
import Button from 'react-bootstrap/Button';
import ConfirmModal from './confirmModal';

class ServerTable extends Component {
  constructor(props) {
    super(props);
    this.state = {
      selected: [],
      buttonName: '',
    };

    this.serverdata = this.props.vpss.filter(
      (vps) => vps.customerName === this.props.customerName
    );
    this.serverdata.forEach((vpss) => {
      if (typeof vpss.dockerStatus == 'undefined') {
        vpss.dockerStatus = 'Undeployed';
      } else {
        vpss.dockerStatus =
        vpss.dockerStatus.charAt(0).toUpperCase() + vpss.dockerStatus.slice(1)
      }
      vpss.deviceStatus =
          vpss.deviceStatus.charAt(0).toUpperCase() + vpss.deviceStatus.slice(1)
    });
    this.aggregateddata = nest()
      .key(function (d) {
        return d.serverName;
      })
      .rollup(function (v) {
        return {
          TotalVPS: v.length,
          CountInactive: sum(v, function (e) {
            return e.deviceStatus === 'INACTIVE';
          }),
          CountToDelete: sum(v, function (e) {
            return e.markToDelete === 'YES';
          }),
        };
      })
      .entries(this.serverdata)
      .map(function (group) {
        return {
          ServerName: group.key,
          TotalVPS: group.value.TotalVPS,
          ServerStatus: 'Active',
          CountInactive: group.value.CountInactive,
          CountToDelete: group.value.CountToDelete,
        };
      });

    this.confirmModalEle = React.createRef();
  }

  // Set state when row(s) is selected in the VPS table
  onRowSelect = ({ VPS }, isSelected, e) => {
    if (isSelected) {
      this.setState({ selected: [...this.state.selected, VPS] });
    } else {
      this.setState({
        selected: this.state.selected.filter((it) => it !== VPS),
      });
    }
  };

  onSelectAll = (isSelected, rows) => {
    if (isSelected) {
      this.setState({
        selected: [...this.state.selected, ...rows.map((row) => row.VPS)],
      });
    } else {
      this.setState({
        selected: this.state.selected.filter(
          (it) => !rows.map((row) => row.VPS).includes(it)
        ),
      });
    }
  };

  // Subtable when VPS table row is expanded
  expandComponent = (row) => {
    var selectRowProp = {
      mode: 'checkbox',
      clickToSelect: true,
      onSelect: this.onRowSelect,
      onSelectAll: this.onSelectAll,
    };

    return (
      <BootstrapTable
        data={this.props.vpss.filter(
          (vps) => vps.serverName === row.ServerName
        )}
        pagination
        selectRow={selectRowProp}
        options={this.options}
        className="expandTable"
      >
        <TableHeaderColumn isKey dataField="VPS" width="20%" dataAlign="center">
          VPS
        </TableHeaderColumn>
        <TableHeaderColumn dataField="GTTmac" width="20%" dataAlign="center">
          GTT mac
        </TableHeaderColumn>

        <TableHeaderColumn
          dataField="deviceStatus"
          width="20%"
          dataAlign="center"
        >
          Set Docker Status
        </TableHeaderColumn>
        <TableHeaderColumn
          dataField="dockerStatus"
          width="20%"
          dataAlign="center"
        >
          Docker Status
        </TableHeaderColumn>
        <TableHeaderColumn
          dataField="markToDelete"
          width="20%"
          dataAlign="center"
        >
          Mark To Delete
        </TableHeaderColumn>
      </BootstrapTable>
    );
  };

  isExpandableRow() {
    return true;
  }

  // Change the visibility of confirmModal
  handleConfirmClick = (element) => {
    this.confirmModalEle.current.handleShow();
    this.setState({ buttonName: element });
  };

  render() {
    return (
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div
          className="ServerTable"
          style={{
            width: '80%',
            marginTop: '1%',
          }}
        >
          <Button
            className="float-right"
            variant="outline-danger"
            value="Delete"
            id="Delete"
            onClick={(e) => this.handleConfirmClick(e.target.value)}
          >
            Delete
          </Button>{' '}
          <Button
            className="float-right"
            variant="outline-primary"
            value="Stop"
            id="Stop"
            onClick={(e) => this.handleConfirmClick(e.target.value)}
          >
            Stop
          </Button>{' '}
          <Button
            className="float-right"
            variant="outline-danger"
            value="Restart"
            id="Restart"
            onClick={(e) => this.handleConfirmClick(e.target.value)}
          >
            Restart
          </Button>{' '}
          <Button
            className="float-right"
            variant="outline-success"
            value="Start"
            id="Start"
            onClick={(e) => this.handleConfirmClick(e.target.value)}
          >
            Start
          </Button>{' '}
          <BootstrapTable
            data={this.aggregateddata}
            striped
            hover
            condensed
            expandableRow={this.isExpandableRow}
            expandComponent={this.expandComponent}
          >
            <TableHeaderColumn
              isKey={true}
              dataField="ServerName"
              dataSort
              width="20%"
              dataAlign="center"
            >
              Server Name
            </TableHeaderColumn>
            <TableHeaderColumn
              dataField="TotalVPS"
              dataSort
              width="20%"
              dataAlign="center"
            >
              Total VPS
            </TableHeaderColumn>
            <TableHeaderColumn
              dataField="ServerStatus"
              width="20%"
              dataAlign="center"
            >
              Server Status
            </TableHeaderColumn>
            <TableHeaderColumn
              dataField="CountInactive"
              width="20%"
              dataAlign="center"
            >
              Count Inactive
            </TableHeaderColumn>
            <TableHeaderColumn
              dataField="CountToDelete"
              width="20%"
              dataAlign="center"
            >
              Count To Delete
            </TableHeaderColumn>
          </BootstrapTable>
          <ConfirmModal
            ref={this.confirmModalEle}
            vpsName={this.state.selected}
            buttonName={this.state.buttonName}
          />
        </div>
      </div>
    );
  }
}

export default ServerTable;
