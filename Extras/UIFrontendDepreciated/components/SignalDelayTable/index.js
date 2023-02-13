import React from "react";
import { Link } from "react-router-dom";
import { Table as AntTable, Typography } from "antd";
import Table from "../../../../common/components/Table";
import TableCard from "../../../../common/components/TableCard";

const { Text } = Typography;

const SignalDelayTable = ({ dataSource, isLoading, ...props }) => {
  const columns = [
    {
      title: "Signal Name",
      dataIndex: "intersection",
      key: "intersection",
      sorter: (a, b) =>
        a.intersection.localeCompare(
          b.intersection,
          navigator.languages[0] || navigator.language,
          { numeric: true, ignorePunctuation: true }
        ),
      sortDirections: ["ascend", "descend"],
      render: (intersection) => (
        <Link key={intersection} to="#" className="btn-analytics">
          {intersection}
        </Link>
      ),
    },
    {
      title: "Avg. Signal Delay(min)",
      dataIndex: "avgSignalDelay",
      key: "avgSignalDelay",
      align: "right",
      render: (avgSignalDelay) => parseFloat(avgSignalDelay).toFixed(0),
      sorter: (a, b) =>
        parseFloat(a.avgSignalDelay) - parseFloat(b.avgSignalDelay),
    },
    {
      title: "Change From Previous Month(min)",
      dataIndex: "change",
      key: "change",
      align: "right",
      render: (change) => Math.round(parseFloat(change) * 100) / 100,
      sorter: (a, b) => parseFloat(a.change) - parseFloat(b.change),
    },
  ];

  const title = "Signal Delay by Intersection";

  return (
    <TableCard
      title={title}
      titleLevel={4}
      table={
        <Table
          {...props}
          pagination={{ position: ["none"] }}
          summary={(pageData) => {
            let totalDelay = 0;
            let totalChange = 0;

            pageData.forEach(({ avgSignalDelay, change }) => {
              totalDelay += parseFloat(avgSignalDelay);
              totalChange += parseFloat(change);
            });

            return (
              <>
                <AntTable.Summary.Row fixed="true" align="right">
                  <AntTable.Summary.Cell></AntTable.Summary.Cell>
                  <AntTable.Summary.Cell>
                    <Text strong>{totalDelay.toFixed(0)} min Total</Text>
                  </AntTable.Summary.Cell>
                  <AntTable.Summary.Cell>
                    <Text strong>{totalChange.toFixed(2)} min</Text>
                  </AntTable.Summary.Cell>
                </AntTable.Summary.Row>
              </>
            );
          }}
          columns={columns}
          dataSource={dataSource}
          rowKey={(record) => record.intersection}
        />
      }
      {...props}
    />
  );
};

export default SignalDelayTable;
