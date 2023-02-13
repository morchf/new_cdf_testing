import React, { useState } from 'react';
import { ReloadOutlined } from '@ant-design/icons';
import { Space, Button as AntButton } from 'antd';
import ConfirmModal from '../VPSConfirmModal';
import { capitalizeFirstLetter } from '../../utils';
import Table from '../../../../common/components/Table';
import ButtonWithTooltip from '../../../../common/components/ButtonWithTooltip';
import useVPSList from '../../hooks/useVPSList';

const isConfigured = (vps) => vps.vpsAvailability !== 'AVAILABLE';
const boolStr = (predicate) => (predicate ? 'YES' : 'NO');

const ServerTable = ({ agyname }) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [selectedNames, setSelectedNames] = useState([]);
  const [buttonName, setButtonName] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  const { vpss, isLoading, edit, editVPSSResponse, refresh } = useVPSList({
    agyname,
  });

  // Change the visibility of confirmModal
  const handleConfirmClick = (element) => {
    setShowConfirmModal(true);
    setButtonName(element);
  };

  const updateDockerStatus = (string) => {
    if (string.toLowerCase() === 'exited') {
      return 'Stopped';
    }
    return capitalizeFirstLetter(string);
  };
  const serverdata = vpss?.map((vps, idx) =>
    'dockerStatus' in vps
      ? {
          ...vps,
          dockerStatus: updateDockerStatus(vps.dockerStatus),
          isConfigured: boolStr(isConfigured(vps)),
          key: idx,
        }
      : {
          ...vps,
          dockerStatus: 'Undeployed',
          isConfigured: boolStr(isConfigured(vps)),
          key: idx,
        }
  );

  const aggServersMap = serverdata?.reduce((r, v, idx) => {
    const aggServer = r[v.serverName] || {
      ServerName: v.serverName,
      ServerStatus: 'Active',
      CountInactive: 0,
      CountToDelete: 0,
      CountAvailable: 0,
      TotalVPS: 0,
      key: idx,
    };
    if (v.deviceStatus === 'INACTIVE') {
      aggServer.CountInactive = +aggServer.CountInactive + 1;
    }
    if (v.markToDelete === 'YES') {
      aggServer.CountToDelete = +aggServer.CountToDelete + 1;
    }
    if (v.isConfigured === 'NO') {
      aggServer.CountAvailable = +aggServer.CountAvailable + 1;
    }

    aggServer.TotalVPS += 1;
    r[v.serverName] = aggServer;
    return r;
  }, {});
  const aggServers = Object.values(aggServersMap || {});

  const onSelectChange = (keys, rows) => {
    setSelectedRowKeys(keys);
    setSelectedNames(rows.map((r) => r.VPS));
  };
  const rowSelection = {
    selectedRowKeys,
    onChange: onSelectChange,
  };
  const expandedRowRender = (row) => {
    const columns = [
      { title: 'VPS', dataIndex: 'VPS', key: 'VPS' },
      { title: 'GTT MAC', dataIndex: 'GTTmac', key: 'GTTmac' },
      {
        title: 'Set Docker Status',
        dataIndex: 'deviceStatus',
        key: 'deviceStatus',
      },
      {
        title: 'Docker Status',
        dataIndex: 'dockerStatus',
        key: 'dockerStatus',
      },
      {
        title: 'Mark To Delete',
        dataIndex: 'markToDelete',
        key: 'markToDelete',
      },
      {
        title: 'Configured',
        dataIndex: 'isConfigured',
        key: 'isConfigured',
      },
    ];

    const data = serverdata.filter((vps) => vps.serverName === row.ServerName);

    return (
      <Table
        columns={columns}
        dataSource={data}
        pagination={true}
        rowSelection={{ ...rowSelection }}
      />
    );
  };

  const columns = [
    { title: 'Server Name', dataIndex: 'ServerName', key: 'ServerName' },
    { title: 'Total VPS', dataIndex: 'TotalVPS', key: 'TotalVPS' },
    { title: 'Server Status', dataIndex: 'ServerStatus', key: 'ServerStatus' },
    {
      title: 'Count Inactive',
      dataIndex: 'CountInactive',
      key: 'CountInactive',
    },
    {
      title: 'Count To Delete',
      dataIndex: 'CountToDelete',
      key: 'CountDelete',
    },
    {
      title: 'Count Available',
      dataIndex: 'CountAvailable',
      key: 'CountAvailable',
    },
  ];
  const hasSelected = selectedRowKeys.length > 0;

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <ButtonWithTooltip
            buttonText="Terminate"
            tooltipText="The docker(s) for the selected VPS will be deleted"
            type="danger"
            onClick={(e) => handleConfirmClick(e.target.innerText)}
            disabled={!hasSelected}
          />
          <ButtonWithTooltip
            buttonText="Stop"
            tooltipText="The docker(s) for the selected VPS will be stopped"
            type="primary"
            onClick={(e) => handleConfirmClick(e.target.innerText)}
            disabled={!hasSelected}
          />
          <ButtonWithTooltip
            buttonText="Restart"
            tooltipText="The docker(s) for the selected VPS will be restarted"
            type="warning"
            onClick={(e) => handleConfirmClick(e.target.innerText)}
            disabled={!hasSelected}
          />
          <ButtonWithTooltip
            buttonText="Start"
            tooltipText="The docker(s) for the selected VPS will be started if they are stopped or missing"
            type="success"
            onClick={(e) => handleConfirmClick(e.target.innerText)}
            disabled={!hasSelected}
          />
          <AntButton
            type="text"
            shape="circle"
            icon={<ReloadOutlined />}
            onClick={refresh}
          />
        </Space>
        <span style={{ marginLeft: 8 }}>
          {hasSelected ? `Selected ${selectedRowKeys.length} VPS` : ''}
        </span>
      </div>

      <Table
        className="components-table-demo-nested"
        columns={columns}
        expandable={{
          expandedRowRender,
          expandRowByClick: true,
          expandIcon: () => <></>,
        }}
        isLoading={isLoading}
        dataSource={aggServers}
        rowKey={(record) => record.ServerName}
      />

      <ConfirmModal
        showConfirmModal={showConfirmModal}
        setShowConfirmModal={setShowConfirmModal}
        response={editVPSSResponse}
        editVPSS={edit}
        vpsName={selectedNames}
        buttonName={buttonName}
      />
    </div>
  );
};

export default ServerTable;
