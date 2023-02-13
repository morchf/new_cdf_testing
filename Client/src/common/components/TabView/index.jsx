import { Radio, Space, Typography as AntTypography } from 'antd';
import { Children } from 'react';
import './style.css';

const { Title: AntTitle } = AntTypography;

export const Header = ({ title, children }) => (
  <div className="tab-view__header">
    {title && (
      <AntTitle className="tab-view__title" level={5}>
        {title}
      </AntTitle>
    )}
    {children}
  </div>
);

// const Tabs = ({ views, value, onChange = () => {}, ...props }) => (
//   <Radio.Group
//     className="tab-view__radio"
//     value={value}
//     onChange={(event) => onChange(event.target.value)}
//     {...props}
//   >
//     <Space direction="vertical" className="tab-view__space">
//       {Children.map(views, (view) => (
//         <Radio.Button
//           className="tab-view__button"
//           value={view.props.value}
//           key={view.props.value}
//         >
//           {view}
//         </Radio.Button>
//       ))}
//     </Space>
//   </Radio.Group>
// );

const TabView = ({
  views,
  onChange,
  value,
  children,
  header,
  isEmpty = false,
  className = '',
  ...props
}) => {
  // Check if any children passed in
  const isContentEmpty =
    isEmpty ||
    !children ||
    // Check for multiple children
    (children?.props?.children?.length &&
      !children.props.children.find((child) => !!child));

  return (
    <section
      className={`tab-view ${className} ${
        isContentEmpty ? 'tab-view--empty' : ''
      }`}
      {...props}
    >
      {header}
      {!isContentEmpty && (
        <div className="tab-view__wrapper">
          {children}
          {/* <div
            className={`tab-view__body ${
              !!header && 'tab-view__body--attached'
            }`}
          >
            {children}
          </div> */}
          {/* <Tabs
            views={views.props.children}
            onChange={onChange}
            value={value}
          /> */}
        </div>
      )}
    </section>
  );
};

export default TabView;
