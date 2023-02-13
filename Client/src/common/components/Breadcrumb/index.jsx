import React, { useMemo } from 'react';
import { Link, useRouteMatch } from 'react-router-dom';
import { Breadcrumb as AntBreadcrumb } from 'antd';
import { BREADCRUMB_TITLES } from '../../constants';
import { capitalize1stLetter } from '../../utils';

const buildBreadcrumbPaths = (pathComponents, pathTemplateComponents) => {
  // Build the path with the components and use to construct relative links
  let currentBuiltPath;

  return pathComponents.map((breadcrumb, i) => {
    const bc = BREADCRUMB_TITLES[breadcrumb];

    // Create link using path components
    currentBuiltPath =
      bc && bc.to ? bc.to : `${currentBuiltPath}/${breadcrumb}`;
    const path = bc?.to || currentBuiltPath;

    // Displayed text
    let text = breadcrumb;
    if (bc?.title) {
      // Use title if available
      text = bc?.title;
    } else if (pathTemplateComponents[i]) {
      // Use param name along path if available
      const paramName = capitalize1stLetter(pathTemplateComponents[i]);
      text = `${paramName} ${breadcrumb}`;
    }

    return {
      key: `${i}-${breadcrumb}`,
      to: path,
      text,
    };
  });
};

const ConfigBreadcrumb = ({
  regionName,
  agencyName,
  vehicleName,
  deviceName,
  intersectionName,
  ...props
}) => (
  <AntBreadcrumb {...props}>
    <AntBreadcrumb.Item>
      <Link to={`/`}>Home</Link>
    </AntBreadcrumb.Item>
    {regionName && (
      <AntBreadcrumb.Item>
        <Link to={`/region/${regionName}`}>{regionName}</Link>
      </AntBreadcrumb.Item>
    )}
    {agencyName && (
      <AntBreadcrumb.Item>
        <Link to={`/region/${regionName}/agency/${agencyName}`}>
          {agencyName}
        </Link>
      </AntBreadcrumb.Item>
    )}
    {vehicleName && (
      <AntBreadcrumb.Item>
        <Link
          to={`/region/${regionName}/agency/${agencyName}/vehicle/${vehicleName}`}
        >
          {vehicleName}
        </Link>
      </AntBreadcrumb.Item>
    )}
    {deviceName && <AntBreadcrumb.Item>{deviceName}</AntBreadcrumb.Item>}
    {intersectionName && (
      <AntBreadcrumb.Item>
        <Link
          to={`/region/${regionName}/agency/${agencyName}/intersections/${intersectionName}`}
        >
          {intersectionName}
        </Link>
      </AntBreadcrumb.Item>
    )}
  </AntBreadcrumb>
);

const Breadcrumb = ({ ...props }) => {
  const routeMatch = useRouteMatch();

  const breadcrumbPaths = useMemo(() => {
    const pathComponents = routeMatch.url
      .split('/')
      .filter((item) => item !== '');

    // Flatten reference to each param (/path/:param1/:param2) -> [path,param1,param2]
    const pathTemplateComponents = routeMatch.path
      .split('/')
      .filter((item) => item !== '')
      .map((item) =>
        item && item.length && item.charAt(0) === ':' ? item.slice(1) : item
      );

    return buildBreadcrumbPaths(pathComponents, pathTemplateComponents);
  }, [routeMatch]);

  return (
    <AntBreadcrumb {...props}>
      {breadcrumbPaths.map(({ key, to, text }, index) => (
        <AntBreadcrumb.Item key={key}>
          {index === 0 ? text : <Link to={to}>{text}</Link>}
        </AntBreadcrumb.Item>
      ))}
    </AntBreadcrumb>
  );
};

Breadcrumb.Config = ConfigBreadcrumb;
export default Breadcrumb;
export { ConfigBreadcrumb };
