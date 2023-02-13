import React, { Component } from 'react';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import axios from 'axios';
import { CMS_URL } from './constants';

class ImportCSV extends Component {
  constructor(props) {
    super(props);
    this.state = {
      importedCSV: null,
      showModal: false,
      Message: '',
      Number: null,
    };
  }
  // import csv file and POST to api
  fileSelectedHandler = (event) => {
    this.setState({
      importedCSV: event.target.files[0],
    });
  };
  fileUploadHandler = async () => {
    try {
      const importedData = await axios.post(CMS_URL, this.state.importedCSV, {
        headers: {
          'Content-Type': 'application/csv',
        },
      });
      this.setState({
        showModal: true,
        Number: importedData.status,
        Message: importedData.data,
      });
    } catch (err) {
      console.log(err);
      this.setState({
        showModal: true,
        Message: err.response.data.errorMessage,
        Number: err.response.data.errorNumber,
      });
    }
  };

  handleClose = () => {
    this.setState({ showModal: false });
  };

  render() {
    return (
      <div style={{ display: 'flex', marginLeft: '10%', marginTop: '1%' }}>
        <div className="ImportCSV">
          <h6 className="text-left">Import Configure File</h6>
          <input type="file" onChange={this.fileSelectedHandler} />
          <Button
            variant="outline-primary"
            type="submit"
            onClick={this.fileUploadHandler}
          >
            Import CSV
          </Button>
          <Modal
            show={this.state.showModal}
            onHide={this.handleClose}
            animation={false}
            style={{
              marginTop: '12%',
            }}
          >
            <Modal.Header closeButton>
              {this.state.Number !== 200 ? 'Error' : 'Success'}
            </Modal.Header>
            <Modal.Body>
              {this.state.Number !== 200 ? this.state.Number + ': ' : ''}
              {this.state.Message}
            </Modal.Body>
            <Modal.Footer>
              <Button variant="primary" onClick={this.handleClose}>
                OK
              </Button>
            </Modal.Footer>
          </Modal>
        </div>
      </div>
    );
  }
}

export default ImportCSV;
