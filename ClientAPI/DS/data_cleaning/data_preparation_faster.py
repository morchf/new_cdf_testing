import pandas as pd
from collections import defaultdict

"""
DATA PREPARATION FUNCTIONS
"""


def get_uid_to_curbreadcrumbs_tsprequest(tripdatas_df):
    uid_to_curbreadcrumbs = tripdatas_df[tripdatas_df["event"] == "TSP request"]
    uid_to_curbreadcrumbs = (
        uid_to_curbreadcrumbs.groupby("uid")["event"].count().reset_index()
    )

    return uid_to_curbreadcrumbs


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


def df_valid_test(df):
    """
    row: row from triplogs
    returns: bool
    valid is a field given in default triplogs dataset. After inspection we understand that:
    if row in triplogs is not valid,
    it has at least one of the following properties:
    1) endstatus == “not started” or endstatus == “aborted”
    2) duration < 0
    """
    return df.valid == True


def end_after_start_test(df):
    return df["starttime"] < df["endtime"]


def endstatus_completed_test(df):
    """
    endstatus can be aborted, completed, not started
    some aborted trips still can be useful becuase it cold be aborted close to the end of the trip
    """
    return df["endstatus"] == "completed"


def tspmode_not_normal_test(df):
    """
    tspmode can be always on, always off, normal
    normal can still be useful when inspecting segments
    """
    return df["tspmode"] != "normal"


def negative_duration_test(df):
    return df["duration"] > 0


def has_enough_breadcrumbs_test(triplogs, tripdatas_count_by_uid):
    """
    return True if in tripdatas there are more rows corresponding to uid in given triplogs_row than
    duration of trip (in seconds) * 0.7. Because ideally we have a row in tripdatas for every second of trip in
    triplogs, but we consider 70% to be enough. Otherwise trip is considered not good for study
    """

    # count number of events because event should occur every second (GPS in particular)
    event_count = triplogs.merge(tripdatas_count_by_uid, on="uid", how="left")["event"]
    return event_count > triplogs["duration"] * 0.7


def hit_enough_stops_test(triplogs):
    """
    if bus has hit more than 70% of stops it was expected to, the trip is considered good
    """
    return triplogs["countstopshit"] / triplogs["stops"] > 0.7


def three_sigmas_cutoff(triplogs, triplogs_grouped):
    """
    in one group (routename + direction) duration of trip are expected to be close t oeach other
    we use statistics (3 standard deviations cutoff) to remove trips with very low or high duration
    compared to others in the group
    triplogs_grouped = {
                        (tripname, direction) as index: [trip durations std]
                       }
    return True if (mean-3*std < triplenth < mean+3*std) else False
    """

    means = triplogs.merge(
        triplogs_grouped.mean().reset_index(), on=["routename", "direction"], how="left"
    )["duration_y"]
    stds = triplogs.merge(
        triplogs_grouped.std(ddof=0).reset_index(),
        on=["routename", "direction"],
        how="left",
    )["duration_y"]
    return ((means - 3 * stds) < triplogs["duration"]) & (
        triplogs["duration"] < (means + 3 * stds)
    )


def tsprequest_occur_for_tspon_test(df, uid_to_curbreadcrumbs_tsprequest):
    """
    if tspmode always on, we want ot make sure
    that intersections with tsp were present on the route
    so we check if tsp requests occured on the route
    """
    is_tsp_req_done = (
        df.merge(uid_to_curbreadcrumbs_tsprequest, on="uid", how="left")["event"] > 0
    )
    return (df["tspmode"] == "alwaysOff") | is_tsp_req_done


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
    triplogs_clean["is_good_for_study"] = True

    # msg is added to reason_not_good_for_study in row where corresponding test failed.
    # Every msg is separated with a coma (,)

    if filtration_dict["row_valid_test"]:
        # drop invalid
        print("drop invalid")
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & df_valid_test(triplogs_clean)

    if filtration_dict["end_after_start_test"]:
        # drop starttime >= endtime
        print("drop starttime >= endtime")
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & end_after_start_test(triplogs_clean)

    if filtration_dict["endstatus_completed_test"]:
        # drop endstatus not completed
        print("drop endstatus not completed")
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & endstatus_completed_test(triplogs_clean)

    if filtration_dict["tspmode_not_normal_test"]:
        # drop normal tspmode
        print("drop normal tspmode")
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & tspmode_not_normal_test(triplogs_clean)

    if filtration_dict["negative_duration_test"]:
        # drop negative duration
        print("drop negative duration")
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & negative_duration_test(triplogs_clean)

    if filtration_dict["hit_enough_stops_test"]:
        # drop <=70% stops hit
        print("drop <=70% stops hit")
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & hit_enough_stops_test(triplogs_clean)

    if filtration_dict["has_enough_breadcrumbs_test"]:
        # drop <=70% breadcrumbs
        print("drop <=70% breadcrumbs")
        tripdatas_count_by_uid = (
            tripdatas_df[tripdatas_df["event"] == "GPS"]
            .groupby("uid")["event"]
            .count()
            .reset_index()
        )
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & has_enough_breadcrumbs_test(triplogs_clean, tripdatas_count_by_uid)

    if filtration_dict["remove_duplicates"]:
        # drop duplicated rows
        print("drop duplicated rows")
        cols_for_detecting_duplicaltes = list(
            set(triplogs_clean.columns) - set(["_id", "uploaddate"])
        )
        is_duplicated_row = triplogs_clean.duplicated(
            subset=cols_for_detecting_duplicaltes, keep="first"
        )
        triplogs_clean["is_good_for_study"] = triplogs_clean["is_good_for_study"] & (
            ~is_duplicated_row
        )

    # if after all checks we still have empty string in reason_not_good_for_study, row is good for study
    # triplogs_clean['is_good_for_study'] = triplogs_clean["reason_not_good_for_study"] == ""

    if filtration_dict["remove_tspon_no_tsprequests"]:
        # drop tspon no tsp requests
        print("drop tspon no tsp requests")
        # msg = ", tspon but no tsp requests"
        uid_to_curbreadcrumbs_tsprequest = get_uid_to_curbreadcrumbs_tsprequest(
            tripdatas_df
        )
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & tsprequest_occur_for_tspon_test(
            triplogs_clean, uid_to_curbreadcrumbs_tsprequest
        )

    if filtration_dict["3_stds"]:
        # drop trips with 3*stds lower and higher of a middle trip time
        print("drop 3 stds anomalies")
        groupby = ["routename", "direction"]
        triplogs_grouped = triplogs_clean[triplogs_clean["is_good_for_study"]].groupby(
            groupby
        )["duration"]
        triplogs_clean["is_good_for_study"] = triplogs_clean[
            "is_good_for_study"
        ] & three_sigmas_cutoff(triplogs_clean, triplogs_grouped)

    return triplogs_clean


def get_clean_tripdatas(tripdatas_df, filtration_dict=defaultdict(lambda: True)):
    tripdatas_clean = tripdatas_df
    if filtration_dict["remove_duplicates"]:
        # drop duplicated rows
        cols_for_detecting_duplicaltes = list(
            set(tripdatas_clean.columns) - set(["_id"])
        )
        is_duplicated_row = tripdatas_clean.duplicated(
            subset=cols_for_detecting_duplicaltes, keep="first"
        )
        tripdatas_clean["is_good_for_study"] = ~is_duplicated_row

    return tripdatas_clean


def get_and_clean_tripdatas_triplogs_merge(
    tripdatas_clean, triplogs_clean, filtration_dict=defaultdict(lambda: True)
):
    merged_df = tripdatas_clean.merge(triplogs_clean, how="inner", on="uid")
    if filtration_dict["remove_routes_mismatch"]:
        # drop trips which do not match on routes
        print("drop trips which do not match on routes")
        is_mismatch = merged_df["routename_y"] != merged_df["routename_x"]
        merged_df["is_good_for_study"] = ~is_mismatch
    return merged_df
