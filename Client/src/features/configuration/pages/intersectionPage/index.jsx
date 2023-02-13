import React, { useState, useCallback, useEffect, useRef } from 'react';
import { withRouter } from 'react-router-dom';
import { PageHeader, Tabs } from 'antd';
import ConfigurationLayout from '../../../../common/layouts/ConfigurationLayout';
import Button from '../../../../common/components/Button';
import MapTabs from '../../../../common/components/MapTabs';
import ApproachesMap from '../../components/ApproachesMap';
import ApproachesGeneral from '../../components/ApproachesGeneral';
import ApproachesThresholds from '../../components/ApproachesThresholds';
import ApproachesOutputs from '../../components/ApproachesOutputs';
import useIntersection from '../../hooks/useIntersection';
import * as defaultIntersectionData from '../../data/defaultDataIntersection.json';
import './style.css';
import openNotification from '../../../../common/components/notification';

const { TabPane } = Tabs;

const Pane = {
  GENERAL: 'general',
  THRESHOLDS: 'thresholds',
  OUTPUTS: 'outputs',
};

// Intersections L2 Page
const IntersectionPage = ({ match }) => {
  const { intersectionId } = match.params;

  const { intersection, isLoading, refresh, update, updateError } =
    useIntersection({
      intersectionId,
    });

  const [isSaved, setIsSaved] = useState(true);
  const [generalData, setGeneralData] = useState();
  const [approachMap, setApproachMap] = useState();
  const [thresholdsData, setThresholdsData] = useState();
  const [outputsData, setOutputsData] = useState();

  useEffect(() => {
    if (!updateError) return;

    openNotification({
      message: 'Error Updating Intersection',
      description: updateError,
    });
  }, [updateError]);

  useEffect(() => {
    if (isLoading) return;
    setIsSaved(false);
  }, [generalData, approachMap, thresholdsData, outputsData, isLoading]);

  useEffect(() => {
    if (isLoading) return;

    setIsSaved(true);
    setGeneralData(
      (({
        intersectionName,
        locationType,
        serialNumber,
        latitude,
        longitude,
        make,
        model,
        timezone,
      }) => ({
        intersectionName,
        locationType,
        serialNumber,
        latitude,
        longitude,
        make,
        model,
        timezone,
      }))(intersection)
    );
    setApproachMap(intersection.approachMap || []);
    setThresholdsData({ ...(intersection.thresholds || {}) });
    setOutputsData({ ...(intersection.outputs || {}) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoading]);

  const onSave = useCallback(() => {
    const newIntersection = { ...intersection, ...generalData };
    newIntersection.approachMap = approachMap;
    newIntersection.thresholds = thresholdsData;
    newIntersection.outputs = outputsData;

    setIsSaved(true);

    update(newIntersection);
  }, [
    approachMap,
    generalData,
    intersection,
    outputsData,
    thresholdsData,
    update,
  ]);

  const onCancel = useCallback(() => {
    refresh();
  }, [refresh]);

  const resetThresholdsToDefaults = () => {
    setThresholdsData(defaultIntersectionData.default.thresholds);
  };

  const resetOutputsToDefaults = () => {
    setOutputsData(defaultIntersectionData.default.outputs);
  };

  const onDelete = () => {
    const resetIntersection = { ...intersection, ...defaultIntersectionData };
    update(resetIntersection);
  };

  return (
    <ConfigurationLayout>
      <div
        className={`approach-container ${
          !isSaved && 'approach-container--unsaved'
        }`}
      >
        {!isSaved && (
          <PageHeader
            title="Approach Map Created"
            extra={[
              <Button key="1" onClick={onSave}>
                Save
              </Button>,
              <Button key="2" type="secondary" onClick={onCancel}>
                Cancel
              </Button>,
              <Button key="3" type="danger" onClick={onDelete}>
                Delete
              </Button>,
            ]}
          />
        )}
        <MapTabs
          defaultActiveKey={Pane.GENERAL}
          tabs={
            <>
              <TabPane tab="General" key={Pane.GENERAL}>
                <ApproachesGeneral
                  isLoading={isLoading}
                  generalData={generalData}
                  onGeneralDataChange={setGeneralData}
                />
              </TabPane>
              <TabPane tab="Thresholds" key={Pane.THRESHOLDS}>
                <ApproachesThresholds
                  thresholdsData={thresholdsData}
                  onThresholdsChange={setThresholdsData}
                  resetToDefaults={resetThresholdsToDefaults}
                />
              </TabPane>
              <TabPane tab="Outputs" key={Pane.OUTPUTS}>
                <ApproachesOutputs
                  outputsData={outputsData}
                  onOutputsChange={setOutputsData}
                  resetToDefaults={resetOutputsToDefaults}
                />
              </TabPane>
            </>
          }
          tabsLoading={isLoading}
          map={
            <ApproachesMap
              isLoading={isLoading}
              lat={isLoading ? 0 : intersection.latitude}
              lng={isLoading ? 0 : intersection.longitude}
              approachMap={approachMap}
              generalData={generalData}
              onApproachMapChange={setApproachMap}
            />
          }
        />
      </div>
    </ConfigurationLayout>
  );
};

export default withRouter(IntersectionPage);
