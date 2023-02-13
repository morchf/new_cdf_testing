import { Link, withRouter } from 'react-router-dom';

const RelativeLink = ({ match, to, children, staticContext, ...props }) => {
  const { url } = match;
  return (
    <Link to={`${url.toString().replace(/\/*$/g, '')}/${to}`} {...props}>
      {children}
    </Link>
  );
};

export default withRouter(RelativeLink);
