import { Steps as AntSteps } from 'antd';

import 'antd/dist/antd.css';
import './style.css';

const { Step: AntStep } = AntSteps;

const RegionsLayout = ({ step = 1, children }) => (
  <main className="regions-layout">
    <AntSteps className="regions-layout__steps" current={step}>
      <AntStep className="regions-layout__step" title="Choose Region" />
      <AntStep title="Choose Agency" />
    </AntSteps>
    <section className="regions-layout__body">{children}</section>
  </main>
);

export default RegionsLayout;
