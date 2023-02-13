import pandas as pd
from collections import defaultdict
import numpy as np
import datetime

"""
DATA PREPARATION FUNCTIONS
"""


def get_uid_to_curbreadcrumbs_stoparrive_depart(tripdatas_df_good):
    uid_to_curbreadcrumbs = defaultdict(list)
    for ind, row in (
        tripdatas_df_good[
            tripdatas_df_good["event"].isin(["stop arrive", "stop depart"])
        ]
        .sort_values("time")
        .iterrows()
    ):
        uid_to_curbreadcrumbs[row["uid"]].append(row)

    for k in uid_to_curbreadcrumbs.keys():
        uid_to_curbreadcrumbs[k] = pd.DataFrame(uid_to_curbreadcrumbs[k])
    return uid_to_curbreadcrumbs


def get_uid_to_curbreadcrumbs_tsprequest(tripdatas_df):
    uid_to_curbreadcrumbs = defaultdict(list)
    for ind, row in tripdatas_df[
        tripdatas_df["event"].isin(["TSP request", "stop arrive", "stop depart"])
    ].iterrows():
        uid_to_curbreadcrumbs[row["uid"]].append(row)

    for k in uid_to_curbreadcrumbs.keys():
        uid_to_curbreadcrumbs[k] = pd.DataFrame(uid_to_curbreadcrumbs[k]).sort_values(
            "time"
        )
    return uid_to_curbreadcrumbs


def get_time_spent_on_busstops(triplog_row, uid_to_curbreadcrumbs):
    """
    triplog_row - row from triplogs
    uid_to_curbreadcrumbs - uid_to_curbreadcrumbs_arrive_depart
    """

    triplog_uid = triplog_row["uid"]
    # routename = triplog_row["routename"]
    # direction = triplog_row["direction"]

    curbreadcrumbs_df = uid_to_curbreadcrumbs[triplog_uid]

    total_time_on_busstops = None

    cur_len = len(curbreadcrumbs_df)
    if cur_len > 0:
        for ind, val in enumerate(curbreadcrumbs_df.iterrows()):
            row = val[1]
            if (
                ind + 1 < cur_len
                and row["event"] == "stop arrive"
                and curbreadcrumbs_df.iloc[ind + 1]["event"] == "stop depart"
            ):
                time_arrived = row["time"]
                time_departed = curbreadcrumbs_df.iloc[ind + 1]["time"]
                total_time_on_busstops = (
                    time_departed - time_arrived
                    if not total_time_on_busstops
                    else total_time_on_busstops + (time_departed - time_arrived)
                )

    return total_time_on_busstops


def prepare_triplogs(triplogs_df):
    """
    transform data format to comfortable and add extra columns to triplogs
    """
    triplogs_df["starttime"] = pd.to_datetime(triplogs_df["starttime"])
    triplogs_df["endtime"] = pd.to_datetime(triplogs_df["endtime"])
    triplogs_df["starthour"] = triplogs_df["starttime"].dt.hour
    # uid (unique id) is used to uniquely identify record and do mapping between triplogs and tripdatas dataset
    triplogs_df["uid"] = triplogs_df["deviceid"] + "_" + triplogs_df["logid"]

    return triplogs_df


def add_columns_to_prepared_triplogs(triplogs_df, tripdatas_df):
    uid_to_curbreadcrumbs_arrive_depart = get_uid_to_curbreadcrumbs_stoparrive_depart(
        tripdatas_df
    )

    triplogs_df["time_spent_on_busstops"] = triplogs_df.apply(
        lambda row: get_time_spent_on_busstops(
            row, uid_to_curbreadcrumbs_arrive_depart
        ),
        axis=1,
    )
    triplogs_df["duration_timedelta"] = triplogs_df.apply(
        lambda row: datetime.timedelta(seconds=row["duration"]), axis=1
    )
    triplogs_df["clear_taveltime"] = (
        triplogs_df["duration_timedelta"] - triplogs_df["time_spent_on_busstops"]
    )
    return triplogs_df


def prepare_tripdatas(tripdatas_df):
    """
    transform data format to comfortable and add extra columns to tripdatas
    """
    # uid (unique id) is used to uniquely identify record and do mapping between triplogs and tripdatas dataset
    tripdatas_df["uid"] = tripdatas_df["deviceid"] + "_" + tripdatas_df["logid"]
    tripdatas_df["time"] = pd.to_datetime(tripdatas_df["time"])

    return tripdatas_df


"""
DATA CLEANING FUNCTIONS
"""

"""
TESTS is rows good for study in triplogs
Every test takes row from triplogs as input and returns True or False
"""


def row_valid_test(row):
    """
    row: row from triplogs
    returns: bool
    valid is a field given in default triplogs dataset. After inspection we understand that:
    if row in triplogs is not valid,
    it has at least one of the following properties:
    1) endstatus == “not started” or endstatus == “aborted”
    2) duration < 0
    """
    return row.valid == True


def end_after_start_test(row):
    return row["starttime"] < row["endtime"]


def endstatus_completed_test(row):
    """
    endstatus can be aborted, completed, not started
    some aborted trips still can be useful becuase it cold be aborted close to the end of the trip
    """
    return row["endstatus"] == "completed"


def tspmode_not_normal_test(row):
    """
    tspmode can be always on, always off, normal
    normal can still be useful when inspecting segments
    """
    return row["tspmode"] != "normal"


def negative_duration_test(row):
    return row["duration"] > 0


def has_enough_breadcrumbs_test(triplogs_row, tripdatas_count_by_uid):
    """
    return True if in tripdatas there are more rows corresponding to uid in given triplogs_row than
    duration of trip (in seconds) * 0.7. Because ideally we have a row in tripdatas for every second of trip in
    triplogs, but we consider 70% to be enough. Otherwise trip is considered not good for study
    """

    # count number of events because event should occur every second (GPS in particular)

    if triplogs_row["uid"] not in tripdatas_count_by_uid.index:
        # means 0 GPS events occurred
        return False
    return (
        tripdatas_count_by_uid.loc[triplogs_row["uid"]]["event"]
        > triplogs_row["duration"] * 0.7
    )


def hit_enough_stops_test(triplogs_row):
    """
    if bus has hit more than 70% of stops it was expected to, the trip is considered good
    """
    return triplogs_row["countstopshit"] / triplogs_row["stops"] > 0.7


def three_sigmas_cutoff(triplogs_row, triplogs_grouped):
    """
    in one group (routename + direction) duration of trip are expected to be close t oeach other
    we use statistics (3 standard deviations cutoff) to remove trips with very low or high duration
    compared to others in the group
    triplogs_grouped = {
                        (tripname, direction) as index: [trip durations array]
                       }
    return True if (mean-3*std < triplenth < mean+3*std) else False
    """
    if (triplogs_row["routename"], triplogs_row["direction"]) in triplogs_grouped.index:
        array = triplogs_grouped.loc[
            triplogs_row["routename"], triplogs_row["direction"]
        ]
        mean, std = np.mean(array), np.std(array)
        return mean - 3 * std < triplogs_row["duration"] < mean + 3 * std
    else:
        return False


def tsprequest_occur_for_tspon_test(row, uid_to_curbreadcrumbs_tsprequest):
    """
    if tspmode always on, we want ot make sure
    that intersections with tsp were present on the route
    so we check if tsp requests occured on the route
    """
    if row["tspmode"] == "alwaysOn":
        if (
            "event" in uid_to_curbreadcrumbs_tsprequest[row["uid"]]
            and "TSP request"
            in uid_to_curbreadcrumbs_tsprequest[row["uid"]]["event"].unique()
        ):
            return True
        else:
            return False
    return True


"""
MAIN FILTRATION FUNCTION
"""


def get_clean_triplogs(
    triplogs_df, tripdatas_df, filtration_dict=defaultdict(lambda: True)
):
    """
    cleans triplogs from data considered abnormal

    filtration_dict: dict with keys corresponding to tests by which filtration is applied and values True (if apply) or False

    Available keys in filtration_dict: "row_valid_test", "end_after_start_test", "endstatus_completed_test",
    "tspmode_not_normal_test", "negative_duration_test", "hit_enough_stops_test", "has_enough_breadcrumbs_test",
    "remove_duplicates", "3_stds"

    By default all filtrations are applied

    If you want not to apply some filtration, pass False as value for some key in defaultdict.
    For example:
    my_filtration_dict = defaultdict(lambda: True)
    my_filtration_dict['row_valid_test'] = False
    """

    triplogs_clean = triplogs_df
    triplogs_clean["reason_not_good_for_study"] = ""

    # msg is added to reason_not_good_for_study in row where corresponding test failed.
    # Every msg is separated with a coma (,)

    if filtration_dict["row_valid_test"]:
        # drop invalid
        print("drop invalid")
        msg = "column valid = False"
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if row_valid_test(row)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )

    if filtration_dict["end_after_start_test"]:
        # drop starttime >= endtime
        print("drop starttime >= endtime")
        msg = ", starttime >= endtime"
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if end_after_start_test(row)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )

    if filtration_dict["endstatus_completed_test"]:
        # drop endstatus not completed
        print("drop endstatus not completed")
        msg = ", endstatus not completed"
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if endstatus_completed_test(row)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )

    if filtration_dict["tspmode_not_normal_test"]:
        # drop normal tspmode
        print("drop normal tspmode")
        msg = ", tspmode not normal"
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if tspmode_not_normal_test(row)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )

    if filtration_dict["negative_duration_test"]:
        # drop negative duration
        print("drop negative duration")
        msg = ", negative duration"
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if negative_duration_test(row)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )

    if filtration_dict["hit_enough_stops_test"]:
        # drop <=70% stops hit
        print("drop <=70% stops hit")
        msg = ", <= 70% stops hit"
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if hit_enough_stops_test(row)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )

    if filtration_dict["has_enough_breadcrumbs_test"]:
        # drop <=70% breadcrumbs
        print("drop <=70% breadcrumbs")
        tripdatas_count_by_uid = (
            tripdatas_df[tripdatas_df["event"] == "GPS"].groupby("uid").count()
        )

        msg = ", <= 70% breadcrumbs"
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if has_enough_breadcrumbs_test(row, tripdatas_count_by_uid)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )

    if filtration_dict["remove_duplicates"]:
        # drop duplicated rows
        print("drop duplicated rows")
        msg = ", duplicated row"
        cols_for_detecting_duplicaltes = list(
            set(triplogs_clean.columns) - set(["_id", "uploaddate"])
        )
        is_duplicated_row = triplogs_clean.duplicated(
            subset=cols_for_detecting_duplicaltes, keep="first"
        )
        triplogs_clean.loc[
            is_duplicated_row, "reason_not_good_for_study"
        ] = triplogs_clean.loc[is_duplicated_row].apply(
            lambda row: row["reason_not_good_for_study"] + msg, axis=1
        )

    # if after all checks we still have empty string in reason_not_good_for_study, row is good for study
    triplogs_clean["is_good_for_study"] = (
        triplogs_clean["reason_not_good_for_study"] == ""
    )

    if filtration_dict["remove_tspon_no_tsprequests"]:
        # drop tspon no tsp requests
        print("drop tspon no tsp requests")
        msg = ", tspon but no tsp requests"
        uid_to_curbreadcrumbs_tsprequest = get_uid_to_curbreadcrumbs_tsprequest(
            tripdatas_df
        )
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if tsprequest_occur_for_tspon_test(row, uid_to_curbreadcrumbs_tsprequest)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )

    if filtration_dict["3_stds"]:
        # drop trips with 3*stds lower and higher of a middle trip time
        print("drop 3 stds anomalies")
        groupby = ["routename", "direction"]
        triplogs_grouped = (
            triplogs_clean[triplogs_clean["is_good_for_study"]]
            .groupby(groupby)["duration"]
            .apply(list)
        )

        msg = ", < or > 3 stds"
        triplogs_clean["reason_not_good_for_study"] = triplogs_clean.apply(
            lambda row: row["reason_not_good_for_study"]
            if three_sigmas_cutoff(row, triplogs_grouped)
            else row["reason_not_good_for_study"] + msg,
            axis=1,
        )
        triplogs_clean["is_good_for_study"] = (
            triplogs_clean["reason_not_good_for_study"] == ""
        )

    triplogs_clean["is_good_for_study"] = (
        triplogs_clean["reason_not_good_for_study"] == ""
    )

    return triplogs_clean


def get_clean_tripdatas(tripdatas_df, filtration_dict=defaultdict(lambda: True)):
    tripdatas_clean = tripdatas_df
    tripdatas_clean["reason_not_good_for_study"] = ""
    if filtration_dict["remove_duplicates"]:
        # drop duplicated rows
        msg = ", duplicated row"
        cols_for_detecting_duplicaltes = list(
            set(tripdatas_clean.columns) - set(["_id"])
        )
        is_duplicated_row = tripdatas_clean.duplicated(
            subset=cols_for_detecting_duplicaltes, keep="first"
        )
        tripdatas_clean.loc[
            is_duplicated_row, "reason_not_good_for_study"
        ] = tripdatas_clean.loc[is_duplicated_row].apply(
            lambda row: row["reason_not_good_for_study"] + msg, axis=1
        )

    # if after all checks we still have empty string in reason_not_good_for_study, row is good for study
    tripdatas_clean["is_good_for_study"] = tripdatas_clean.apply(
        lambda row: row["reason_not_good_for_study"] == "", axis=1
    )

    return tripdatas_clean
