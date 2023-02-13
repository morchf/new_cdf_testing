import numpy as np
import pandas as pd
from copy import deepcopy

# this library contain two approaches for GPS path smoothing: Kalman and optimisation


class Kalman_filter:
    def __init__(self):
        # P, Q and R matrises may be tuned
        # P - initial uncertainty, will be quickly recalculated
        # cols - x, x', x'', y, y', y''
        # x - measurement, x' - velosity, x'' - acceleration
        self.P = np.array(
            [
                [100, 0, 0, 0, 0, 0],
                [0, 100, 0, 0, 0, 0],
                [0, 0, 100, 0, 0, 0],
                [0, 0, 0, 100, 0, 0],
                [0, 0, 0, 0, 100, 0],
                [0, 0, 0, 0, 0, 100],
            ]
        )
        dt = 1.0

        self.F = np.array(
            [
                [1, dt, dt ** 2 / 2, 0, 0, 0],
                [0, 1, dt, 0, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 0, 0, 1, dt, dt ** 2 / 2],
                [0, 0, 0, 0, 1, dt],
                [0, 0, 0, 0, 0, 1],
            ]
        )

        self.H = np.array([[1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0]])

        # R - measurement variation matrix, should meet actual data variance (for x and y measurement)
        self.R = np.array([[0.001, 0], [0, 0.001]])

        # Q - dynamic model noise matrix, "how uncertain kalman filtering must be"
        # higher values smooth more
        self.Q = np.array(
            [
                [0, 0, 0, 0, 0, 0],
                [0, 0.001, 0, 0, 0, 0],
                [0, 0, 0.001, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0.001, 0],
                [0, 0, 0, 0, 0, 0.001],
            ]
        )

        self.I = np.array(
            [
                [1, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
            ]
        )

        self.u = np.array([[0.0], [0.0], [0.0], [0.0], [0.0], [0.0]])

        self.x = np.array([[0.0], [0.0], [0.0], [0.0], [0.0], [0.0]])

    def estimate(self, measurement):

        Z = np.array(measurement)
        Z = Z.reshape(-1, 1)

        # update
        y = Z - (self.H @ self.x)
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + (K @ y)

        self.P = (self.I - (K @ self.H)) @ self.P

        # prediction
        self.x = (self.F @ self.x) + self.u
        self.P = self.F @ self.P @ self.F.T + self.Q

        return self.x


def smooth(path, weight_data=0.005, weight_smooth=0.9, tolerance=0.000000001):
    newpath = deepcopy(path)
    change = 10000000000
    while change > tolerance:
        change = 0
        for i in range(1, len(path) - 1):
            for j in range(len(path[0])):
                prev = newpath[i][j]
                newpath[i][j] += weight_data * (
                    path[i][j] - newpath[i][j]
                ) + weight_smooth * (
                    newpath[i - 1][j] + newpath[i + 1][j] - 2.0 * newpath[i][j]
                )
                change += abs(prev - newpath[i][j])
    return newpath


if __name__ == "__main__":
    k = Kalman_filter()
    df = pd.read_csv(
        "/Users/ailin/Documents/grid-dynamics/DS/BusStops/bus_stop_maps/14R/all_14R_inbound_20210501-t3_4010KJ0999.csv"
    )
    # make [[x, y], [x1, y2], ...] list
    xys = df[["lon", "lat"]].values.tolist()

    # Kalman
    lst = []
    # pass measurements in reversed order to smooth starting measurements
    for i, (lon, lat) in enumerate(xys[::-1]):
        lon1, _, _, lat1, _, _ = k.estimate((lon, lat))
        lst.append([lon1, lat1])

    # revert list
    xys = np.array(lst[::-1])

    # # smoothing
    # xys = smooth(xys)
    # xys = np.array(xys)

    df["lon"] = xys[:, 0]
    df["lat"] = xys[:, 1]
    df.to_csv("path_smoother_smooth.csv")
