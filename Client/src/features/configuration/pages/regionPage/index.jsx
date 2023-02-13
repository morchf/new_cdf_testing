import React, { useState, useEffect, useCallback } from 'react';
import { connect } from 'react-redux';
import { Breadcrumb as AntBreadcrumb, Typography as AntTypography } from 'antd';
import { withRouter, Link } from 'react-router-dom';
import EditRegion from '../../components/EditRegion';
import AgencyTableForRegion from '../../components/AgencyTableForRegion';
import CreateAgencyModal from '../../components/CreateAgencyModal';
import RegionsLayout from '../../../../common/layouts/RegionsLayout';
import ConfirmModal from '../../components/ConfirmModal';
import RegionsControls from '../../../../common/components/RegionsControls';
import openNotification from '../../../../common/components/notification';
import useRegion from '../../hooks/useRegion';
import useAgencies from '../../hooks/useAgencies';

const { Title: AntTitle } = AntTypography;

const Breadcrumb = ({ region, regionName, regname }) => (
  <AntBreadcrumb>
    <AntBreadcrumb.Item>
      <Link to="/">Regions</Link>
    </AntBreadcrumb.Item>
    {region && (
      <AntBreadcrumb.Item>
        <Link to={`/region/${regname}`}>{regionName}</Link>
      </AntBreadcrumb.Item>
    )}
  </AntBreadcrumb>
);

const RegionPage = ({ match }) => {
  const {
    params: { regname },
  } = match;

  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [selected, setSelected] = useState([]);
  const [searchTerm, setSearchTerm] = useState();

  // load region data
  let params = `/groups/%2F${regname}`;
  const {
    region,
    isLoading: regionIsLoading,
    isError: regionIsError,
    error: regionError,
    editRegionResponse,
    edit: editRegion,
  } = useRegion({ params });

  // load agencies data
  params = `/groups/%2F${regname}/members/groups`;
  const {
    agencies,
    agenciesList,
    isLoading: agenciesIsLoading,
    isError: agenciesIsError,
    error: agenciesError,
    createAgencyResponse,
    createAgency,
    deleteAgencyResponse,
    deleteAgency,
  } = useAgencies({ params });

  useEffect(() => {
    if (regionIsError)
      openNotification({
        message: 'Error Getting Region',
        description: regionError.message,
      });
  }, [regionError?.message, regionIsError]);

  useEffect(() => {
    if (agenciesIsError)
      openNotification({
        message: 'Error Getting Agencies',
        description: agenciesError.message,
      });
  }, [agenciesError?.message, agenciesIsError]);

  const filteredAgencies = !agenciesList
    ? []
    : agenciesList.filter(
        ({ Name: name }) =>
          !searchTerm || name.toLowerCase().includes(searchTerm)
      );

  const handleResponseChange = useCallback(() => {
    setCreating(false);
  }, [setCreating]);

  // Change the visibility of confirmModal
  const handleConfirmClick = () => {
    setDeleting(true);
  };

  const confirmBody = {
    agencies: selected ? selected.map((agency) => `${regname}/${agency}`) : [],
  };

  const regionName = region ? region.name : '';

  return (
    <>
      <CreateAgencyModal
        regionName={regionName}
        agencies={agencies || []}
        onResponseChange={handleResponseChange}
        onCancel={() => setCreating(false)}
        visible={creating}
        createAgency={createAgency}
        response={createAgencyResponse}
      />

      <ConfirmModal
        visible={deleting}
        onResponseChange={() => setDeleting(false)}
        onSelectedChange={() => setSelected([])}
        body={confirmBody}
        selected={selected}
        delete={deleteAgency}
        response={deleteAgencyResponse}
      />

      <RegionsLayout step={1}>
        <div>
          <Breadcrumb
            region={region || []}
            regionName={regionName}
            regname={regname}
          />
          <AntTitle style={{ marginTop: '2rem' }}>Region {regionName}</AntTitle>
          {region && (
            <EditRegion
              region={region}
              editRegion={editRegion}
              response={editRegionResponse}
            />
          )}
        </div>

        <RegionsControls
          label={'Agency'}
          onSearch={(st) => setSearchTerm(st.toLowerCase())}
          onCreate={() => setCreating(true)}
          onDelete={handleConfirmClick}
        />

        <div>
          <AntTitle level={5} style={{ margin: '0.5rem 0 1.25rem 0' }}>
            Agency
          </AntTitle>
          <AgencyTableForRegion
            loading={agenciesIsLoading}
            regionName={regionName}
            agencies={filteredAgencies}
            selected={selected}
            onSelectedChange={(value) => setSelected(value)}
          />
        </div>
      </RegionsLayout>
    </>
  );
};

const mapStateToProps = (state) => ({
  response: state.response,
});

export default connect(mapStateToProps)(withRouter(RegionPage));
