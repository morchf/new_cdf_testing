import React, { Component } from 'react';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';

class ServerSubtable extends Component {
  constructor(props) {
    super(props);
    this.options = {
      defaultSortName: 'ServerName', // default sort column name
      defaultSortOrder: 'desc', // default sort order
    };
  }

  render() {
    console.log(this.props.serverVPSS);

    return (
      <div className="ServerSubtable">
        <p>{this.props.data}</p>
        <BootstrapTable
          data={rowdata}
          striped
          hover
          condensed
          options={this.options}
        >
          <TableHeaderColumn isKey dataField="customerName" dataSort>
            Customer Name
          </TableHeaderColumn>
          <TableHeaderColumn dataField="serverName" dataSort>
            Server Name
          </TableHeaderColumn>
          <TableHeaderColumn dataField="VPS">VPS</TableHeaderColumn>
          <TableHeaderColumn dataField="primaryKey">
            Primary Key
          </TableHeaderColumn>
          <TableHeaderColumn dataField="markToDelete">
            Mark To Delete
          </TableHeaderColumn>
          <TableHeaderColumn dataField="deviceStatus">
            Device Status
          </TableHeaderColumn>
        </BootstrapTable>
      </div>
    );
  }
}

export default ServerSubtable;
