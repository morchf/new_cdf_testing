import React, { Component } from 'react';
import {
  select,
  nest,
  sum,
  max,
  scaleLinear,
  set,
  scaleBand,
  axisBottom,
  axisLeft,
} from 'd3';

class Barchart extends Component {
  constructor(props) {
    super(props);
  }

  // create object server
  draw() {
    const customerdata = this.props.vpss;
    const data = nest()
      .key(function (d) {
        return d.customerName;
      })
      .rollup(function (v) {
        return {
          ServerNumber: set(v, function (e) {
            return e.serverName;
          }).size(),
          TotalVPC: v.length,
          CountInactive: sum(v, function (e) {
            return e.deviceStatus === 'INACTIVE';
          }),
          CountToDelete: sum(v, function (e) {
            return e.markToDelete === 'YES';
          }),
        };
      })
      .entries(customerdata)
      .map(function (group) {
        return {
          CustomerName: group.key,
          ServerNumber: group.value.ServerNumber,
          TotalVPC: group.value.TotalVPC,
          CountInactive: group.value.CountInactive,
          CountToDelete: group.value.CountToDelete,
        };
      });

    const node = select(this.node);
    const width = 400;
    const height = 300;
    let a = this.props.xaxisname,
      b = this.props.yaxisname;
    let xValue = d => d[a];
    let yValue = d => d[b];

    const margin = { top: 30, right: 20, bottom: 50, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const xScale = scaleLinear()
      .domain([0, max(data, xValue)])
      .range([0, innerWidth]);

    const yScale = scaleBand()
      .domain(data.map(yValue))
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
      .data(data)
      .enter()
      .append('rect')
      .attr('y', d => yScale(yValue(d)))
      .attr('width', d => xScale(xValue(d)))
      .attr('height', yScale.bandwidth());

    g.append('text')
      .attr('y', -5)
      .text(a + ' By Customer');
  }

  componentDidUpdate() {
    this.draw();
  }

  render() {
    return (
      <svg
        className="Barchart"
        style={{ width: '400', height: '300' }}
        ref={node => {
          this.node = node;
        }}
      ></svg>
    );
  }
}

export default Barchart;
