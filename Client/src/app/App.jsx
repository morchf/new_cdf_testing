import React, { Fragment } from 'react';
import { Switch, Route, BrowserRouter } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';
import { Provider } from 'react-redux';
import { errorHandler } from '../common/utils';
import ScrollToTop from '../common/components/scrollToTop';
import Login from '../features/userAuth/components/Login';
import LoginCallback from '../features/userAuth/components/LoginCallback';
import RegionPage from '../features/configuration/pages/regionPage';
import RegionsPage from '../features/configuration/pages/regionsPage';
import ScheduleDeviationOverviewPage from '../features/scheduleDeviation/pages/overview';
import ScheduleDeviationRouteDetailsPage from '../features/scheduleDeviation/pages/routeDetails';
import ScheduleDeviationStopDetailsPage from '../features/scheduleDeviation/pages/stopDetails';
import PrivateRoute from '../features/navigation/components/PrivateRoute';
import NavHeader from '../features/navigation/components/NavHeader';
import NavLayout from '../features/navigation/components/NavLayout';
import SignalDelayOverviewPage from '../features/travelTime/pages/overview';
import SignalDelayRouteDetailsPage from '../features/travelTime/pages/routeDetails';
import ErrorPage from '../features/errorPage';

/** @todo - REMAIN COMMENTED UNTIL RELEASED */
// import IntersectionsPage from '../features/healthMonitoring/pages/intersectionsPage';
import VehiclesHealthMonitoringPage from '../features/healthMonitoring/pages/vehiclesHealthMonitoringPage';
import VPSPage from '../features/configuration/pages/vpsPage';
import IntersectionsPage from '../features/configuration/pages/intersectionsPage';
import IntersectionPage from '../features/configuration/pages/intersectionPage';
import VehiclesPage from '../features/configuration/pages/vehiclesPage';
import AgencyPage from '../features/configuration/pages/agencyPage';

import store from '../redux/store';
import AuthListener from '../features/userAuth/components/AuthListener';

export default function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <ErrorBoundary FallbackComponent={ErrorPage} onError={errorHandler}>
          <AuthListener>
            <ScrollToTop />
            <div style={{ height: '100%', width: '100%' }}>
              <Switch>
                <Route path="/login">
                  <Login />
                </Route>
                <Route path="/callback">
                  <LoginCallback />
                </Route>
                {/* Client Services Admin Routes */}
                <PrivateRoute exact path="/">
                  <Fragment>
                    <NavHeader />
                    <RegionsPage />
                  </Fragment>
                </PrivateRoute>
                <PrivateRoute exact path="/region/:regname">
                  <Fragment>
                    <NavHeader />
                    <RegionPage />
                  </Fragment>
                </PrivateRoute>

                <PrivateRoute path="/analytics">
                  <NavLayout>
                    {/* Analytics - Schedule Deviation */}
                    <PrivateRoute exact path="/analytics/schedule-deviation">
                      <ScheduleDeviationOverviewPage />
                    </PrivateRoute>
                    <PrivateRoute
                      exact
                      path="/analytics/schedule-deviation/:route"
                    >
                      <ScheduleDeviationRouteDetailsPage />
                    </PrivateRoute>
                    <PrivateRoute
                      exact
                      path="/analytics/schedule-deviation/:route/stop/:stop"
                    >
                      <ScheduleDeviationStopDetailsPage />
                    </PrivateRoute>

                    {/* Analytics - Transit Delay */}
                    <PrivateRoute exact path="/analytics/transit-delay">
                      <SignalDelayOverviewPage />
                    </PrivateRoute>
                    <PrivateRoute exact path="/analytics/transit-delay/:route">
                      <SignalDelayRouteDetailsPage />
                    </PrivateRoute>
                    {/* <PrivateRoute exact path="/analytics/transit-delay/:route/intersection/:intersection" /> */}
                  </NavLayout>
                </PrivateRoute>

                {/* Configuration - visible to only Admin users*/}
                <PrivateRoute path="/region">
                  <NavLayout>
                    <PrivateRoute exact path="/region/:regname/agency/:agyname">
                      <AgencyPage />
                    </PrivateRoute>

                    {/* Intersections */}
                    <PrivateRoute
                      exact
                      path="/region/:regname/agency/:agyname/intersections"
                    >
                      <IntersectionsPage />
                    </PrivateRoute>
                    <PrivateRoute
                      exact
                      path="/region/:regname/agency/:agyname/intersections/:intersectionId"
                    >
                      <IntersectionPage />
                    </PrivateRoute>

                    {/* Vehicles */}
                    <PrivateRoute
                      exact
                      path="/region/:regname/agency/:agyname/vehicles"
                    >
                      <VehiclesPage />
                    </PrivateRoute>

                    <PrivateRoute
                      exact
                      path="/region/:regname/agency/:agyname/vps"
                    >
                      <VPSPage />
                    </PrivateRoute>
                  </NavLayout>
                </PrivateRoute>

                {/* Health Monitoring - REMAIN COMMENTED UNTIL RELEASED */}
                {/* <PrivateRoute exact path="/health-monitoring/intersections">
                <IntersectionsPage />
            </PrivateRoute> */}

                <PrivateRoute path="/health-monitoring">
                  <NavLayout>
                    {/* Metrics - Schedule Deviation */}
                    <PrivateRoute exact path="/health-monitoring/vehicles">
                      <VehiclesHealthMonitoringPage />
                    </PrivateRoute>
                  </NavLayout>
                </PrivateRoute>

                {/* Error Routes */}
                <Route path="*">
                  <ErrorPage />
                </Route>
              </Switch>
            </div>
          </AuthListener>
        </ErrorBoundary>
      </BrowserRouter>
    </Provider>
  );
}
