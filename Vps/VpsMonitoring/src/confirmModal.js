import React, { Component } from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import axios from 'axios';
import VPS_API from './constants';

const buttonMap = {
  Delete: 'YES',
  Start: 'ACTIVE',
  Restart: 'RESTART',
  Stop: 'INACTIVE',
};

class ConfirmModal extends Component {
  constructor(props) {
    super(props);
    this.state = {
      showButtonModal: false,
      showResponseModal: false,
      showErrorModal: false,
      response: '',
    };
  }

  // buttoms to start/restart/stop/delete
  handleButtonClick = (event) => {
    if (this.props.vpsName.length === 0) {
      this.setState({ showErrorModal: true, showButtonModal: false });
    } else {
      const final_res = this.props.vpsName.forEach(async (name) => {
        const res = await axios.put(VPS_API, {
          VPSName: name,
          dockerStatus: buttonMap[this.props.buttonName],
        });
        this.setState({
          showButtonModal: false,
          response: res.data,
          showResponseModal: true,
        });
      });
      console.log(final_res);
    }
  };

  handleClose = () => {
    this.setState({ showButtonModal: false });
  };
  handleShow = () => {
    this.setState({ showButtonModal: true });
  };

  handleResponseClose = () => {
    this.setState({ showResponseModal: false });
    window.location.reload(false);
  };
  handleErrorClose = () => {
    this.setState({ showErrorModal: false });
  };

  render() {
    return (
      <div className="Modals">
        <div className="ButtonModal">
          <Modal
            show={this.state.showButtonModal}
            onHide={this.handleClose}
            animation={false}
            style={{
              marginTop: '12%',
            }}
          >
            <Modal.Header closeButton>
              {this.props.buttonName}
              {' File'}
            </Modal.Header>
            <Modal.Body>
              {`Are you sure you want to ${this.props.buttonName.toLowerCase()} the ${this.props.vpsName.length} VPS?`}
            </Modal.Body>
            <Modal.Footer>
              <Button
                className="button-cancel"
                variant="secondary"
                onClick={this.handleClose}
              >
                Cancel
              </Button>
              <Button variant="primary" onClick={this.handleButtonClick}>
                Confirm
              </Button>
            </Modal.Footer>
          </Modal>
        </div>
        <div className="ResponseModal">
          <Modal
            show={this.state.showResponseModal}
            onHide={this.handleResponseClose}
            animation={false}
            style={{
              marginTop: '12%',
            }}
          >
            <Modal.Header closeButton></Modal.Header>
            <Modal.Body>
              {this.state.response.endsWith(
                'device status successfully updated'
              )
                ? 'Device status successfully updated'
                : this.state.response}
            </Modal.Body>
            <Modal.Footer>
              <Button variant="primary" onClick={this.handleResponseClose}>
                OK
              </Button>
            </Modal.Footer>
          </Modal>
        </div>
        <div className="ErrorModal">
          <Modal
            show={this.state.showErrorModal}
            onHide={this.handleErrorClose}
            animation={false}
            style={{
              marginTop: '12%',
            }}
          >
            <Modal.Header closeButton>Error</Modal.Header>
            <Modal.Body>You should select one VPS at a time.</Modal.Body>
            <Modal.Footer>
              <Button variant="primary" onClick={this.handleErrorClose}>
                OK
              </Button>
            </Modal.Footer>
          </Modal>
        </div>
      </div>
    );
  }
}
export default ConfirmModal;
