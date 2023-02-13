import React from 'react';
import { nest, set, sum } from 'd3';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';

const CustomerTable = (props) => {
  const items = props;
  const customerdata = nest()
    .key(function (d) {
      return d.customerName;
    })
    .rollup(function (v) {
      return {
        ServerNumber: set(v, function (e) {
          return e.serverName;
        }).size(),
        TotalVPS: v.length,
        CountInactive: sum(v, function (e) {
          return e.deviceStatus === 'INACTIVE';
        }),
        CountToDelete: sum(v, function (e) {
          return e.markToDelete === 'YES';
        }),
      };
    })
    .entries(items.vpss)
    .map(function (group) {
      return {
        CustomerName: group.key,
        ServerNumber: group.value.ServerNumber,
        TotalVPS: group.value.TotalVPS,
        CountInactive: group.value.CountInactive,
        CountToDelete: group.value.CountToDelete,
      };
    });

  return (
    <div
      className="box"
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <div
        className="CustomerTable"
        style={{
          width: '80%',
          marginTop: '5%',
        }}
      >
        <BootstrapTable data={customerdata} striped hover condensed>
          <TableHeaderColumn
            isKey
            dataField="CustomerName"
            dataSort
            width="20%"
            dataAlign="center"
          >
            Customer Name
          </TableHeaderColumn>
          <TableHeaderColumn
            dataField="ServerNumber"
            dataSort
            width="20%"
            dataAlign="center"
          >
            Server Number
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
            dataField="CountInactive"
            dataSort
            width="20%"
            dataAlign="center"
          >
            Count Inactive
          </TableHeaderColumn>
          <TableHeaderColumn
            dataField="CountToDelete"
            dataSort
            width="20%"
            dataAlign="center"
          >
            Count To Delete
          </TableHeaderColumn>
        </BootstrapTable>
      </div>
    </div>
  );
};

export default CustomerTable;
