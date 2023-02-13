import React, { Component } from "react";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import axios from "axios";
import { Form, Col } from "react-bootstrap";
import { VPS_URL } from "../../common/constants";

class Provision extends Component {
  constructor(props) {
    super(props);
    this.state = {
      devicePrefix: "",
      count: "",
      showModal: false,
      Message: "",
      Number: null,
    };
  }
  // Create new vps and POST to api
  deviceSelectedHandler = (event) => {
    this.setState({ devicePrefix: event.target.value });
  };
  countSelectedHandler = (event) => {
    this.setState({ count: event.target.value });
  };
  handleSubmit = async (event) => {
    try {
      event.preventDefault();
      const updatedData = await axios.post(VPS_URL, {
        customer: this.props.customerName,
        deviceprefix: this.state.devicePrefix,
        number: parseInt(this.state.count),
      });
      this.setState({
        showModal: true,
        Number: updatedData.status,
        Message: updatedData.data,
      });
    } catch (err) {
      console.log(err.response);
      this.setState({
        showModal: true,
        Message: err.response.data,
        Number: err.response.status,
      });
    }
  };

  handleClose = () => {
    this.setState({ showModal: false });
  };
  handleUpdateClose = () => {
    this.setState({ showModal: false });
  };

  render() {
    return (
      <div style={{ display: "flex", marginLeft: "10%", marginTop: "3%" }}>
        <div className="Provison">
          <h6 className="text-left">Provison</h6>
          <Form className="border" span={12} width="80%">
            <Form.Row>
              <Form.Group as={Col} md={6} controlId="DevicePrefix">
                <Form.Label className="float-left">Device Prefix</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="V764"
                  value={this.state.devicePrefix}
                  onChange={this.deviceSelectedHandler}
                />
              </Form.Group>

              <Form.Group as={Col} md={6} controlId="Count">
                <Form.Label className="float-left">Count</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="50"
                  value={this.state.count}
                  onChange={this.countSelectedHandler}
                />
              </Form.Group>
            </Form.Row>
            <Form.Row>
              <Col md="auto">
                <Button
                  variant="outline-primary"
                  type="submit"
                  onClick={this.handleSubmit}
                >
                  Submit
                </Button>
              </Col>
            </Form.Row>
          </Form>
          <Modal
            show={this.state.showModal}
            onHide={this.handleClose}
            animation={false}
            style={{
              marginTop: "12%",
            }}
          >
            <Modal.Header closeButton>
              {this.state.Number !== 200 ? "Error" : "Success"}
            </Modal.Header>
            <Modal.Body>{this.state.Message}</Modal.Body>
            <Modal.Footer>
              <Button variant="primary" onClick={this.handleUpdateClose}>
                OK
              </Button>
            </Modal.Footer>
          </Modal>
        </div>
      </div>
    );
  }
}

export default Provision;
