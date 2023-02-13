/* eslint-disable no-nested-ternary */
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Form as AntForm,
  Select as AntSelect,
  Input as AntInput,
  TimePicker,
  Card,
  Col,
  Row,
  Button,
} from 'antd';
import moment from 'moment';
import openNotification from '../../../../common/components/notification';
import {
  setTimeperiod,
  setOnTimeRange,
} from '../../../featurePersistence/store/slice';
import { accessLocalStorage } from '../../../../common/utils';
import 'antd/dist/antd.css';
import './style.css';

const EditAgencySettings = ({
  editFeaturePersistanceTSP,
  createFPResponse,
  data,
}) => {
  const { dataresponse, isSuccess, isError, error, status } = createFPResponse;
  const [scheduleDeviationButton, setScheduleDeviationButton] = useState(false);
  const [earlyScheduleDeviation, setEarlyScheduleDeviation] = useState(
    data?.Feature?.early_schedule_deviation_limit?.toString() ?? '0'
  );
  const [lateScheduleDeviation, setLateScheduleDeviation] = useState(
    data?.Feature?.late_schedule_deviation_limit?.toString() ?? '0'
  );
  const { agencyGuid } = useSelector(({ user }) => user);
  useEffect(() => {
    if (isSuccess) {
      if (scheduleDeviationButton) {
        openNotification({
          message: 'Schedule Deviation Data Updated',
          type: 'success',
        });
      } else {
        openNotification({
          message: 'Peak Hours Data Updated',
          type: 'success',
        });
      }
    }
  }, [data]);

  useEffect(() => {
    if (isError) {
      openNotification({
        message: 'Error while updating agency settings',
        description: error.message,
      });
    }
  }, [error?.message, isError, createFPResponse, status]);

  const { storeLocalItem, getLocalItem } = accessLocalStorage();
  const dispatch = useDispatch();
  const handleFormSubmit = (values) => {
    const attributes = { ...values };
    const skeleton = {};
    skeleton.FeatureName = 'tsp-analytics';
    skeleton.AgencyGUID = agencyGuid;
    const skeletonAttributes = { ...skeleton.Feature };
    const peakPmRange = {};
    const peakAmRange = {};

    if (scheduleDeviationButton) {
      skeletonAttributes.early_schedule_deviation_limit =
        attributes.early_schedule_deviation_limit;
      skeletonAttributes.late_schedule_deviation_limit =
        attributes.late_schedule_deviation_limit;
      peakAmRange.start_time = data?.Feature?.peak_am_range?.start_time;
      peakAmRange.end_time = data?.Feature?.peak_am_range?.end_time;
      peakPmRange.start_time = data?.Feature?.peak_pm_range?.start_time;
      peakPmRange.end_time = data?.Feature?.peak_pm_range?.end_time;
      dispatch(
        setOnTimeRange([
          attributes.early_schedule_deviation_limit,
          attributes.late_schedule_deviation_limit,
        ])
      );
    } else {
      peakAmRange.start_time = attributes.PeakAMFrom.format('HH:mm:ss');
      peakAmRange.end_time = attributes.PeakAMTo.format('HH:mm:ss');
      peakPmRange.start_time = attributes.PeakPMFrom.format('HH:mm:ss');
      peakPmRange.end_time = attributes.PeakPMTo.format('HH:mm:ss');
      skeletonAttributes.early_schedule_deviation_limit =
        data?.Feature?.early_schedule_deviation_limit;
      skeletonAttributes.late_schedule_deviation_limit =
        data?.Feature?.late_schedule_deviation_limit;
      dispatch(
        setTimeperiod([
          {
            start_time: peakAmRange.start_time,
            label: 'peak_am',
            end_time: peakAmRange.end_time,
          },
          {
            start_time: peakPmRange.start_time,
            label: 'peak_pm',
            end_time: peakPmRange.end_time,
          },
        ])
      );
    }

    skeletonAttributes.peak_pm_range = peakPmRange;
    skeletonAttributes.peak_am_range = peakAmRange;
    skeleton.Feature = skeletonAttributes;
    editFeaturePersistanceTSP(skeleton);
  };

  const EarlyScheduleDeviationDropdown = (event) => {
    setEarlyScheduleDeviation(event);
  };

  const LateScheduleDeviationDropdown = (event) => {
    setLateScheduleDeviation(event);
  };

  const generateSelectOptions = (range, multiplier) => {
    const selectOptions = [];
    for (let i = 1; i < range + 1; i++) {
      selectOptions.push(
        <AntSelect.Option
          key={i * multiplier}
          value={(i * multiplier).toString()}
        >
          {multiplier === 1 ? '+' : ''}
          {i * multiplier} min
        </AntSelect.Option>
      );
    }
    return selectOptions;
  };

  return (
    <AntForm
      name="basic"
      autoComplete="off"
      onFinish={handleFormSubmit}
      initialValues={{
        late_schedule_deviation_limit:
          data?.Feature?.late_schedule_deviation_limit?.toString(),
        early_schedule_deviation_limit:
          data?.Feature?.early_schedule_deviation_limit?.toString(),
        PeakAMFrom: moment(
          data?.Feature?.peak_am_range?.start_time,
          'HH:mm:ss'
        ),
        PeakAMTo: moment(data?.Feature?.peak_am_range?.end_time, 'HH:mm:ss'),
        PeakPMFrom: moment(
          data?.Feature?.peak_pm_range?.start_time,
          'HH:mm:ss'
        ),
        PeakPMTo: moment(data?.Feature?.peak_pm_range?.end_time, 'HH:mm:ss'),
      }}
    >
      <Row gutter={20}>
        <Col span={10}>
          <div className="site-card-border-less-wrapper">
            <Row gutter={24}>
              <Col className="gutter-row" span={19}>
                <p className="card-title">Schedule Deviation</p>
              </Col>
              <Col className="gutter-row" span={3}>
                <AntForm.Item>
                  <Button
                    type="primary"
                    onClick={() => setScheduleDeviationButton(true)}
                    htmlType="submit"
                  >
                    SAVE
                  </Button>
                </AntForm.Item>
              </Col>
            </Row>
            <div style={{ marginTop: '-3%' }}>
              <Card>
                <div className="card-padding-bottom">
                  <Row gutter={20}>
                    <Col className="gutter-row" span={10}>
                      <AntForm.Item
                        label={<b>Late ≥</b>}
                        name="late_schedule_deviation_limit"
                      >
                        <AntSelect onChange={LateScheduleDeviationDropdown}>
                          {generateSelectOptions(10, -1)}
                        </AntSelect>
                      </AntForm.Item>
                    </Col>
                    <Col className="gutter-row" span={10}>
                      <AntForm.Item
                        label={<b>Early ≥</b>}
                        name="early_schedule_deviation_limit"
                      >
                        <AntSelect onChange={EarlyScheduleDeviationDropdown}>
                          {generateSelectOptions(5, 1)}
                        </AntSelect>
                      </AntForm.Item>
                    </Col>
                  </Row>
                </div>
              </Card>
            </div>

            <div className="card-padding-top">
              <Card>
                <div
                  className="card-padding-bottom"
                  style={{ paddingBottom: '2em' }}
                >
                  <Row gutter={24}>
                    <Col span={8}>
                      <b>On-time range = </b>
                    </Col>
                    <Col span={5}>
                      <div className="box">{lateScheduleDeviation} min</div>
                    </Col>
                    <Col span={2}>
                      <b>to</b>
                    </Col>
                    <Col span={5}>
                      <div className="box">+{earlyScheduleDeviation} min</div>
                    </Col>
                  </Row>
                </div>
              </Card>
            </div>
          </div>
        </Col>
        <Col span={10}>
          <div className="site-card-border-less-wrapper">
            <Row gutter={24}>
              <Col className="gutter-row" span={19}>
                <p className="card-title">Peak Hours</p>
              </Col>
              <Col className="gutter-row" span={3}>
                <AntForm.Item>
                  <Button
                    type="primary"
                    onClick={() => setScheduleDeviationButton(false)}
                    htmlType="submit"
                  >
                    SAVE
                  </Button>
                </AntForm.Item>
              </Col>
            </Row>
            <div style={{ marginTop: '-3%' }}>
              <Card>
                <div className="card-padding-bottom">
                  <Row gutter={24}>
                    <Col className="gutter-row" span={14}>
                      <AntForm.Item
                        label={<b>Peak AM from</b>}
                        name="PeakAMFrom"
                      >
                        <TimePicker
                          use12Hours
                          format="h:mm A"
                          minuteStep={30}
                        />
                      </AntForm.Item>
                    </Col>
                    <Col className="gutter-row" span={10}>
                      <AntForm.Item label={<b>to</b>} name="PeakAMTo">
                        <TimePicker
                          use12Hours
                          format="h:mm A"
                          minuteStep={30}
                        />
                      </AntForm.Item>
                    </Col>
                  </Row>
                </div>
              </Card>
            </div>
            <div className="card-padding-top">
              <Card>
                <div className="card-padding-bottom">
                  <Row gutter={24}>
                    <Col className="gutter-row" span={14}>
                      <AntForm.Item
                        label={<b>Peak PM from</b>}
                        name="PeakPMFrom"
                      >
                        <TimePicker
                          use12Hours
                          format="h:mm A"
                          minuteStep={30}
                        />
                      </AntForm.Item>
                    </Col>
                    <Col className="gutter-row" span={10}>
                      <AntForm.Item label={<b>to</b>} name="PeakPMTo">
                        <TimePicker
                          use12Hours
                          format="h:mm A"
                          minuteStep={30}
                        />
                      </AntForm.Item>
                    </Col>
                  </Row>
                </div>
              </Card>
            </div>
          </div>
        </Col>
      </Row>
    </AntForm>
  );
};

export default EditAgencySettings;
