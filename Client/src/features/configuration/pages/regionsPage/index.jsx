import React, { useState, useEffect, useCallback } from 'react';
import { connect } from 'react-redux';
import { Link, withRouter } from 'react-router-dom';
import { Typography as AntTypography } from 'antd';
import CreateRegionModal from '../../components/CreateRegionModal';
import ConfirmModal from '../../components/ConfirmModal';
import RegionsLayout from '../../../../common/layouts/RegionsLayout';
import RegionsControls from '../../../../common/components/RegionsControls';
import ImportCSV from '../../components/ImportCSV';
import { BATCH_URL } from '../../../../common/constants';
import Table, { alphanumericSorter } from '../../../../common/components/Table';
import { setAdminRegion } from '../../../userAuth/store/slice';
import openNotification from '../../../../common/components/notification';
import useRegions from '../../hooks/useRegions';

const { Title: AntTitle } = AntTypography;

const RegionsPage = ({ onAdminRegionChange = () => {} }) => {
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [selected, setSelected] = useState([]);
  const [searchTerm, setSearchTerm] = useState();

  const params = '/groups/%2F/members/groups';
  const {
    regions,
    isLoading,
    isError,
    error,
    createRegionResponse,
    createRegion,
    deleteRegionResponse,
    deleteRegion,
  } = useRegions({ params });

  useEffect(() => {
    if (isError)
      openNotification({
        message: 'Error Getting Regions',
        description: error.message,
      });
  }, [error?.message, isError]);

  const filteredRegions = !regions
    ? []
    : regions.filter(
        ({ name }) => !searchTerm || name.toLowerCase().includes(searchTerm)
      );

  const rowSelection = {
    selectedRowKeys: selected,
    onChange: (value) => setSelected([...value]),
  };

  const handleResponseChange = useCallback(() => {
    setCreating(false);
  }, [setCreating]);

  // Change the visibility of confirmModal
  const handleConfirmClick = () => {
    setDeleting(true);
  };

  const columns = [
    {
      dataIndex: 'name',
      title: 'Region Name',
      key: 'name',
      render: (_text, record) => {
        const handleClick = () => {
          onAdminRegionChange(record.name.toLowerCase());
        };
        return (
          <Link
            to={`/region/${record.name.toLowerCase()}`}
            onClick={handleClick}
            className="btn-analytics"
            key={record.name}
          >
            {record.name}
          </Link>
        );
      },
      defaultSortOrder: 'ascend',
      sorter: alphanumericSorter('name'),
    },
    {
      dataIndex: 'description',
      title: 'Description',
      key: 'description',
    },
  ];

  const confirmBody = { regions: selected || [] };

  return (
    <>
      <CreateRegionModal
        visible={creating}
        onResponseChange={handleResponseChange}
        onCancel={() => setCreating(false)}
        createRegion={createRegion}
        response={createRegionResponse}
      />

      <ConfirmModal
        visible={deleting}
        onResponseChange={() => setDeleting(false)}
        onSelectedChange={() => setSelected([])}
        body={confirmBody}
        selected={selected}
        delete={deleteRegion}
        response={deleteRegionResponse}
      />

      <RegionsLayout step={0}>
        <RegionsControls
          label={'Region'}
          onSearch={(st) => setSearchTerm(st.toLowerCase())}
          onCreate={() => setCreating(true)}
          onDelete={handleConfirmClick}
        />

        <div>
          <AntTitle level={5} style={{ margin: '0.5rem 0 1.25rem 0' }}>
            Region
          </AntTitle>
          <Table
            style={{ width: '100%' }}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              defaultPageSize: 20,
            }}
            isLoading={isLoading}
            columns={columns}
            rowKey={(value) => value.name}
            dataSource={filteredRegions}
            rowSelection={rowSelection}
          />
          <div>
            <ImportCSV title="Batch Create Entities" uploadURL={BATCH_URL} />
          </div>
        </div>
      </RegionsLayout>
    </>
  );
};

const mapStateToProps = (state) => ({
  response: state.response,
});
const mapDispatchToProps = {
  onAdminRegionChange: (regionName) => (dispatch) =>
    dispatch(setAdminRegion(regionName)),
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(withRouter(RegionsPage));
