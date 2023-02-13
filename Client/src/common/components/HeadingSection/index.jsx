import React, { memo } from 'react';
import { Link, useRouteMatch } from 'react-router-dom';
import { Affix, Typography as AntTypography } from 'antd';
import Back from '../../icons/Back';
import InfoTooltip from '../InfoTooltip';
import './style.css';

const { Title: AntTitle } = AntTypography;

const HeadingSection = ({
  title,
  subTitle,
  backTo,
  backToLastPath,
  tooltip,
  above,
  metrics,
  children,
}) => {
  const routeMatch = useRouteMatch();
  const lastPath = routeMatch.url
    .split('/')
    .filter((item) => item !== '')
    .slice(0, -1)
    .join('/');

  return (
    <>
      <div className="heading-section__breadcrumb">{above}</div>
      {title && (
        <Affix offsetTop={35}>
          <section className="heading-section">
            <div className="heading-section__body">
              <div className="heading-wrapper">
                <div className="back-button">
                  {(backToLastPath || backTo) && (
                    <Link to={backTo || lastPath}>
                      <Back />
                    </Link>
                  )}
                </div>
                <AntTitle className="heading-section__title" level={2}>
                  {title}
                </AntTitle>
                {tooltip && <InfoTooltip text={tooltip} />}
              </div>
              {subTitle && <AntTitle level={5}>{subTitle}</AntTitle>}
              {children && (
                <div className="bottom-component-wrapper">{children}</div>
              )}
              {metrics && <div style={{ width: '100%' }}>{metrics}</div>}
            </div>
          </section>
        </Affix>
      )}
    </>
  );
};

export default memo(HeadingSection);
