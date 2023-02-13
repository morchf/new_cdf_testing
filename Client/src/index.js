import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import 'antd/dist/antd.css';
import { Amplify } from 'aws-amplify';
import { config } from './features/userAuth/config';
import App from './app/App';

Amplify.configure(config);

ReactDOM.render(<App />, document.getElementById('root'));
