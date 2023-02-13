import React, { useState, useEffect } from "react";
import { Form as AntForm, Input as AntInput, Select as AntSelect } from "antd";
import FormModal from "../../../../common/components/FormModal";
import { editDeviceSchema } from "../../schemas";
import openNotification from "../../../../common/components/notification";
import Button from "../../../../common/components/Button";
import Table from "../../../../common/components/Table";
import "./style.css";

const EditDevice = ({ device, editDevice, response }) => {
  const [showEditTable, setShowEditTable] = useState(false);
  const [windowSize, setWindowSize] = useState(undefined);
  const [model, setModel] = useState("");
  const { data, isLoading, isSuccess, isError, error } = response;

  if (device && device.attributes.model !== model && !showEditTable)
    setModel(device.attributes.model);

  useEffect(() => {
    if (isSuccess) {
      openNotification({
        message: data,
        type: "success",
      });
      setShowEditTable(false);
    }
  }, [data, isSuccess]);

  useEffect(() => {
    if (isError)
      openNotification({
        message: "Error Editing Device",
        description: error.message,
      });
  }, [error?.message, isError]);

  useEffect(() => {
    const handleResize = async (e) => {
      setWindowSize(window.innerWidth);
    };

    window.addEventListener("resize", handleResize);
  }, []);

  const onSubmit = async (values) => {
    const body = { ...device };
    const attributes = { ...body.attributes };
    if (values.description !== "") {
      body.description = values.description;
    }
    if (values.gttSerial !== "") {
      attributes.gttSerial = values.gttSerial;
    }
    if (values.serial !== "") {
      attributes.serial = values.serial;
    }
    if (values.addressMAC !== "") {
      attributes.addressMAC = values.addressMAC;
    } else if (values.make === "GTT") {
      attributes.addressMAC = "";
    }
    if (values.IMEI !== "") {
      attributes.IMEI = values.IMEI;
    } else if (values.make === "GTT") {
      attributes.IMEI = "";
    }
    if (values.addressLAN !== "") {
      attributes.addressLAN = values.addressLAN;
    }
    if (values.addressWAN !== "") {
      attributes.addressWAN = values.addressWAN;
    }
    if (values.make !== "") {
      attributes.make = values.make;
    }
    if (values.make === "GTT" && model === "MP-70") {
      attributes.model = "2100";
    } else if (values.make === "GTT") {
      attributes.model = values.model;
    } else if (values.make === "Sierra Wireless") {
      attributes.model = "MP-70";
    } else if (values.make === "Cradlepoint") {
      attributes.model = values.model;
    }
    body.attributes = { ...attributes };
    editDevice(body);
  };

  const columns = [
    {
      key: "key",
      dataIndex: "key",
      title: "GTT Serial",
    },
    {
      key: "serial",
      dataIndex: "serial",
      title: "Serial",
    },
    {
      key: "make",
      dataIndex: "make",
      title: "Make",
    },
    {
      key: "model",
      dataIndex: "model",
      title: "Model",
    },
    {
      key: "addressLAN",
      dataIndex: "addressLAN",
      title: "LAN Address",
    },
    {
      key: "addressWAN",
      dataIndex: "addressWAN",
      title: "WAN Address",
    },
    {
      key: "description",
      dataIndex: "description",
      title: "Description",
    },
    {
      key: "addressMAC",
      dataIndex: "addressMAC",
      title: "MAC Address",
    },
    {
      key: "IMEI",
      dataIndex: "IMEI",
      title: "IMEI",
    },
  ];

  function DeviceTable({ device: d }) {
    const tableItems =
      !d || d.length === 0
        ? null
        : [
            {
              key: d.attributes.gttSerial,
              description: d.description,
              ...d.attributes,
            },
          ];
    return (
      <div className="DeviceTable">
        <Table
          columns={columns}
          dataSource={tableItems}
          pagination={false}
          bordered={false}
          scroll={windowSize < 1600 ? { x: 1200 } : {}}
        />
      </div>
    );
  }

  return (
    <div className="Edit">
      {showEditTable ? (
        <FormModal
          title="Edit Device"
          onSubmit={onSubmit}
          visible={showEditTable}
          onCancel={() => setShowEditTable(false)}
          loading={isLoading}
          validationSchema={editDeviceSchema}
          validateOnChange={false}
          initialValues={{
            description: device.description,
            gttSerial: device.attributes.gttSerial,
            serial: device.attributes.serial,
            addressMAC: device.attributes.addressMAC,
            addressLAN: device.attributes.addressLAN,
            addressWAN: device.attributes.addressWAN,
            IMEI: device.attributes.IMEI,
            make: device.attributes.make,
            model: device.attributes.model,
          }}
        >
          {({
            handleSubmit,
            handleChange,
            values,
            errors,
            isSubmitting,
            setFieldValue,
          }) => (
            <div>
              <AntForm
                labelCol={{ span: 6 }}
                wrapperCol={{ span: 12 }}
                onSubmit={handleSubmit}
                onChange={handleChange}
              >
                <AntForm.Item label="GTT Serial" help={errors.gttSerial}>
                  <AntInput
                    type="text"
                    name="gttSerial"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.gttSerial}
                  />
                </AntForm.Item>
                <AntForm.Item label="Serial" help={errors.serial}>
                  <AntInput
                    type="text"
                    name="serial"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.serial}
                  />
                </AntForm.Item>
                <AntForm.Item label="Make" help={errors.priority}>
                  <AntSelect
                    name="make"
                    disabled={isSubmitting}
                    onChange={(value) => setFieldValue("make", value)}
                    value={values.make}
                  >
                    <AntSelect.Option value="Cradlepoint">
                      Cradlepoint
                    </AntSelect.Option>
                    <AntSelect.Option value="GTT">GTT</AntSelect.Option>
                    <AntSelect.Option value="Sierra Wireless">
                      Sierra Wireless
                    </AntSelect.Option>
                  </AntSelect>
                </AntForm.Item>
                {values.make === "Sierra Wireless" ? (
                  <AntForm.Item label="Model" help={errors.model}>
                    <AntSelect
                      name="model"
                      disabled={isSubmitting}
                      onChange={(value) => setFieldValue("model", value)}
                      defaultValue={values.model}
                    >
                      <AntSelect.Option value="MP-70">MP-70</AntSelect.Option>
                    </AntSelect>
                  </AntForm.Item>
                ) : values.make === "Cradlepoint" ? (
                  <AntForm.Item label="Model" help={errors.model}>
                    <AntSelect
                      name="model"
                      disabled={isSubmitting}
                      onChange={(value) => setFieldValue("model", value)}
                      defaultValue={values.model}
                    >
                      <AntSelect.Option value="IBR900">IBR900</AntSelect.Option>
                      <AntSelect.Option value="IBR1700">
                        IBR1700
                      </AntSelect.Option>
                      <AntSelect.Option value="R1900">R1900</AntSelect.Option>
                    </AntSelect>
                  </AntForm.Item>
                ) : values.make === "GTT" ? (
                  <AntForm.Item label="Model" help={errors.model}>
                    <AntSelect
                      name="model"
                      disabled={isSubmitting}
                      onChange={(value) => setFieldValue("model", value)}
                      defaultValue={values.model}
                    >
                      <AntSelect.Option value="2100">2100</AntSelect.Option>
                      <AntSelect.Option value="2101">2101</AntSelect.Option>
                    </AntSelect>
                  </AntForm.Item>
                ) : null}
                {values.make !== "GTT" &&
                values.make !== "Sierra Wireless" &&
                values.make !== "Cradlepoint" ? (
                  <AntForm.Item label="Model" help={errors.model}>
                    <AntSelect
                      name="model"
                      disabled={isSubmitting}
                      onChange={(value) => setFieldValue("model", value)}
                      defaultValue={values.model}
                    >
                      <AntSelect.Option value="Null"></AntSelect.Option>
                    </AntSelect>
                  </AntForm.Item>
                ) : null}

                <AntForm.Item label="LAN Address" help={errors.addressLAN}>
                  <AntInput
                    type="text"
                    name="addressLAN"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.addressLAN}
                  />
                </AntForm.Item>
                <AntForm.Item label="WAN Address" help={errors.addressWAN}>
                  <AntInput
                    type="text"
                    name="addressWAN"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.addressWAN}
                  />
                </AntForm.Item>
                <AntForm.Item label="Description" help={errors.description}>
                  <AntInput
                    type="text"
                    name="description"
                    onChange={handleChange}
                    disabled={isSubmitting}
                    value={values.description}
                  />
                </AntForm.Item>
                {values.make === "Sierra Wireless" && (
                  <>
                    <AntForm.Item label="MAC Address" help={errors.addressMAC}>
                      <AntInput
                        type="text"
                        name="addressMAC"
                        onChange={handleChange}
                        disabled={isSubmitting}
                        value={values.addressMAC}
                      />
                    </AntForm.Item>
                    <AntForm.Item label="IMEI" help={errors.IMEI}>
                      <AntInput
                        type="text"
                        name="IMEI"
                        onChange={handleChange}
                        disabled={isSubmitting}
                        value={values.IMEI}
                      />
                    </AntForm.Item>
                  </>
                )}
              </AntForm>
            </div>
          )}
        </FormModal>
      ) : (
        <div>
          <h5>Device Properties</h5>
          <DeviceTable device={device} />
          <Button
            type="secondary"
            size="lg"
            location="right"
            onClick={() => setShowEditTable(true)}
          >
            Edit Properties
          </Button>
        </div>
      )}
    </div>
  );
};

export default EditDevice;
