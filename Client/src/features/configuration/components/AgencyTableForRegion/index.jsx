import React from 'react';
import { connect } from 'react-redux';
import { withRouter, Link } from 'react-router-dom';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import { setAdminAgency } from '../../../userAuth/store/slice';

const AgencyTableForRegion = ({
  loading,
  agencies,
  match,
  selected,
  onSelectedChange,
  onAdminAgencyChange = () => {},
}) => {
  const { url } = match;
  const rowSelection = {
    selectedRowKeys: selected,
    onChange: (value) => onSelectedChange([...value]),
  };

  const columns = [
    {
      dataIndex: 'Name',
      key: 'name',
      title: 'Name',
      render: (_text, record) => {
        const agency = {
        "name" : record.Name.toLowerCase(),
        "agencyGuid" : record.agencyID,}
        const handleClick = () => {
          onAdminAgencyChange(agency);
        };
        return (
          <Link
            to={`${url}/agency/${record.Name.toLowerCase()}`}
            onClick={handleClick}
            className="btn-analytics"
            key={record.Name}
          >
            {record.Name}
          </Link>
        );
      },
      onFilter: (value, record) =>
        record.name
          ? record.name.toString().toLowerCase().includes(value.toLowerCase())
          : '',
      defaultSortOrder: 'ascend',
      sorter: alphanumericSorter('Name'),
    },
    {
      dataIndex: 'description',
      key: 'description',
      title: 'Description',
    },
    {
      dataIndex: 'city',
      key: 'city',
      title: 'City',
      sorter: alphanumericSorter('city'),
    },
    {
      dataIndex: 'state',
      key: 'state',
      title: 'State',
      sorter: alphanumericSorter('state'),
    },
    {
      dataIndex: 'timezone',
      key: 'timezone',
      title: 'Time Zone',
    },
    {
      dataIndex: 'agencyCode',
      key: 'agencyCode',
      title: 'Agency Code',
      sorter: alphanumericSorter('agencyCode'),
    },
    {
      dataIndex: 'priority',
      key: 'priority',
      title: 'Priority',
      sorter: alphanumericSorter('priority'),
    },
    {
      dataIndex: 'CMSId',
      key: 'CMSId',
      title: 'CMS Id',
    },
  ];

  return (
    <section style={{ overflowX: 'scroll' }}>
      {!loading && (!agencies || agencies.length === 0) ? (
        <p>No associated agency</p>
      ) : (
        <Table
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            defaultPageSize: 20,
          }}
          isLoading={loading}
          columns={columns}
          rowKey={(value) => value.Name}
          dataSource={agencies}
          rowSelection={rowSelection}
        />
      )}
    </section>
  );
};

const mapStateToProps = ({ user }) => {
  const { region, agency, AgencyGUID } = user;
  return { region, agency, AgencyGUID };
};

const mapDispatchToProps = {
  onAdminAgencyChange: (agency) => (dispatch) =>
    dispatch(setAdminAgency(agency)),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withRouter(AgencyTableForRegion));
