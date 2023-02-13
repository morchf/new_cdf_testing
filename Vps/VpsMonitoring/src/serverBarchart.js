import React, { Component } from 'react';
import {
  select,
  nest,
  sum,
  max,
  scaleLinear,
  scaleBand,
  axisBottom,
  axisLeft,
} from 'd3';
import './barchart.css';

class ServerBarchart extends Component {
  constructor(props) {
    super(props);

    const serverdata = this.props.vpss.filter(
      (vps) => vps.customerName === this.props.customerName
    );
    this.data = nest()
      .key(function (d) {
        return d.serverName;
      })
      .rollup(function (v) {
        return {
          TotalVPS: v.length,
          CountInactive: sum(v, function (e) {
            return e.deviceStatus === 'INACTIVE';
          }),
          CountToDelete: sum(v, function (e) {
            return e.markToDelete === 'YES';
          }),
        };
      })
      .entries(serverdata)
      .map(function (group) {
        return {
          ServerName: group.key,
          TotalVPS: group.value.TotalVPS,
          ServerStatus: 'ACTIVE',
          CountInactive: group.value.CountInactive,
          CountToDelete: group.value.CountToDelete,
        };
      });
  }

  componentDidMount() {
    this.draw();
  }

  // create object server
  draw() {
    const node = select(this.node);
    const width = 400;
    const height = 300;
    const a = this.props.xaxisname;
    const b = this.props.yaxisname;
    const xValue = (d) => d[a];
    const yValue = (d) => d[b];

    const margin = { top: 30, right: 20, bottom: 50, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const xScale = scaleLinear()
      .domain([0, max(this.data, xValue)])
      .range([0, innerWidth]);

    const yScale = scaleBand()
      .domain(this.data.map(yValue))
      .range([0, innerHeight])
      .padding(0.2);

    const g = node
      .append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const xAxis = axisBottom(xScale).tickSize(-innerHeight);

    g.append('g')
      .call(axisLeft(yScale))
      .selectAll('.domain, .tick line')
      .remove();

    const xAxisG = g
      .append('g')
      .call(xAxis)
      .attr('transform', `translate(0, ${innerHeight})`);

    xAxisG.select('.domain').remove();

    xAxisG
      .append('text')
      .attr('class', 'axis-label')
      .attr('y', 35)
      .attr('x', innerWidth / 2)
      .attr('fill', 'black')
      .text(a);

    g.selectAll('rect')
      .data(this.data)
      .enter()
      .append('rect')
      .attr('y', (d) => yScale(yValue(d)))
      .attr('width', (d) => xScale(xValue(d)))
      .attr('height', yScale.bandwidth());

    g.append('text').attr('y', -5).text(`${a} By Customer`);
  }

  render() {
    return (
      <svg
        className="Barchart"
        style={{ width: '400', height: '300' }}
        ref={(node) => {
          this.node = node;
        }}
      />
    );
  }
}

export default ServerBarchart;
