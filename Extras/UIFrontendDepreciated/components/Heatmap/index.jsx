import React, { useState, useEffect, memo } from 'react';
import { Heatmap } from '@ant-design/charts';
import {
  Card,
  Nav,
  Navbar,
  Dropdown,
  DropdownButton,
  InputGroup,
  Form,
  Button,
  Col,
} from 'react-bootstrap';
import { Link } from 'react-router-dom';
import mockData from '../../data/mockDataHeatMap';
import './style.css';

const HealthHeatmap = () => {
  const [data, setData] = useState([]);
  const [title, setTitle] = useState(['Select time range']);
  const asyncFetch = () => {
    setData(mockData);
  };

  useEffect(() => {
    asyncFetch();
  }, []);

  useEffect(() => {
    setTitle(title);
  }, [title]);

  const config = {
    width: 650,
    height: 250,
    autoFit: true,
    data,
    xField: 'Date',
    yField: 'Intersection',
    legend: { position: 'top-left' },
    colorField: 'TSP Requests',
    label: {
      style: {
        fill: '#000000',
        shadowBlur: 2,
        shadowColor: 'rgba(0, 0, 0, .45)',
      },
    },
    color: [
      '#cb3541',
      '#d55d67',
      '#e0868d',
      '#f2cccf',
      '#faebec',
      '#e6edef',
      '#bfcfd7',
      '#668e9f',
      '#33687f',
      '#00425f',
    ],
    meta: { Date: { type: 'cat' } },
  };

  return (
    <Card>
      <Card.Header>
        <Card.Body>
          <Card.Title>Intersection(s)</Card.Title>
          <br />
          <Card.Text>
            {' '}
            Filter intersections by selecting on map or search below:
          </Card.Text>
          <Col md={6}>
            <InputGroup>
              <Form.Control
                placeholder="Type intersection name"
                aria-label="Type intersection name"
                aria-describedby="basic-addon2"
              />
              <InputGroup.Append>
                <Button variant="outline-primary">Search</Button>
              </InputGroup.Append>
            </InputGroup>
          </Col>
        </Card.Body>
        <br />
        <Navbar>
          <Nav className="mr-auto">
            <Nav.Item>
              <Link to="#" className="nav-link">
                Details
              </Link>
            </Nav.Item>
            <Nav.Item>
              <Link to="#" className="nav-link">
                Status History
              </Link>
            </Nav.Item>
            <Nav.Item>
              <Link to="#" className="nav-link">
                Firmware History
              </Link>
            </Nav.Item>
            <Nav.Item>
              <Link to="#" className="nav-link">
                TSP Request Heat Map
              </Link>
            </Nav.Item>
          </Nav>
          <Nav>
            <DropdownButton variant="outline-secondary" title={title}>
              <Dropdown.Item as="button">
                <div onClick={() => setTitle('Past week')}>Past week</div>
              </Dropdown.Item>
              <Dropdown.Item as="button">
                <div onClick={() => setTitle('Past 30 days')}>Past 30 days</div>
              </Dropdown.Item>
              <Dropdown.Item as="button">
                <div onClick={() => setTitle('Year to date')}>Year to date</div>
              </Dropdown.Item>
            </DropdownButton>
          </Nav>
        </Navbar>
      </Card.Header>
      <br />
      <div className="heatmap-text">
        <ul>
          <li>
            Number of priority requests made low to high, color coded from red
            to blue, intersection list sorted alphabetically
          </li>
          <li>
            Weekends tend to have fewer requests due to fewer scheduled headways
          </li>
          <li>
            Washington and Maryland are one-way streets which have fewer
            priority requests
          </li>
          <li>
            Intersections showing dark red for consecutive days can indicate no
            logged data and troubleshooting is required{' '}
          </li>
        </ul>
      </div>
      <div className="heatmap-container">
        <Heatmap {...config} />
      </div>
    </Card>
  );
};

export default memo(HealthHeatmap);
