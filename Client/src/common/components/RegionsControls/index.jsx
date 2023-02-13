import { Button as AntButton, Input as AntInput } from 'antd';
import './style.css';

const { Search: AntSearch } = AntInput;

const RegionsControls = ({ label, onSearch, onCreate, onDelete }) => (
  <div className="regions-controls">
    <div className="regions-controls__search-bar">
      {label && `${label}:`}
      <AntSearch
        className="regions-controls__search"
        placeholder="Please enter"
        allowClear
        size="large"
        onSearch={onSearch}
      />
    </div>
    <div className="regions-controls__buttons">
      <AntButton className="regions-controls__button" danger onClick={onDelete}>
        Delete
      </AntButton>
      <AntButton
        className="regions-controls__button"
        type="primary"
        onClick={onCreate}
      >
        Create New
      </AntButton>
    </div>
  </div>
);

export default RegionsControls;
