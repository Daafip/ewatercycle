import os
from datetime import datetime

import numpy as np
import pandas as pd
import xarray as xr


def get_grdc_data(station_id,
                  start_date,
                  end_date,
                  parameter='Q',
                  cache_dir=None):
    """
    Get data from GRDC

    Parameters
    ----------
    station_id : str
        The station id to get
    start_date : str
        String for start date in the format: 'YYYY-MM-dd', e.g. '1980-01-01'
    end_date : str
        String for start date in the format: 'YYYY-MM-dd', e.g. '2018-12-31'
    parameter : str, optional
        The parameter code to get, e.g. ('Q') discharge, cubic meters per second
    cache_dir : str, optional
        The directory where the daily grdc data is located.
        If left out will use the environment variable GRDC_DATA_HOME

    Examples
    --------
    >>> from ewatercycle.observation.grdc import get_grdc_data
    >>> data = get_grdc_data('6335020', '2000-01-01', '2001-01-01', cache_dir='.')
    >>> data
        <xarray.Dataset>
        Dimensions:     (time: 367)
        Coordinates:
        * time        (time) datetime64[ns] 2000-01-01 2000-01-02 ... 2001-01-01
        Data variables:
            streamflow  (time) float64 ...
        Attributes:
            grdc_file_name:                6335020_Q_Day.Cmd
            id_from_grdc:                  6335020
            file_generation_date:          2019-03-27
            river_name:                    RHINE RIVER
            station_name:                  REES
            country_code:                  DE
            grdc_latitude_in_arc_degree:   51.756918
            grdc_longitude_in_arc_degree:  6.395395
            grdc_catchment_area_in_km2:    159300.0
            altitude_masl:                 8.0
            dataSetContent:                MEAN DAILY DISCHARGE (Q)
            units:                         m�/s
            time_series:                   1814-11 - 2016-12
            no_of_years:                   203
            last_update:                   2018-05-24
            nrMeasurements:                NA
    """
    if cache_dir is None:
        cache_dir = os.environ['GRDC_DATA_HOME']

    # Check if we have the netcdf data
    netcdf = os.path.join(cache_dir, station_id + "_" + parameter + "_Day.nc")
    if os.path.exists(netcdf):
        return xr.open_dataset(netcdf)

    # Download the data if needed
    cmd = os.path.join(cache_dir, station_id + "_" + parameter + "_Day.Cmd")
    # Convert the raw data to an xarray
    metadata, df = _grdc_read(
        cmd,
        start=datetime.strptime(start_date, "%Y-%m-%d"),
        end=datetime.strptime(end_date, "%Y-%m-%d"))

    # Create the xarray dataset
    ds = df.to_xarray()
    ds.attrs = metadata

    ds.to_netcdf(netcdf)

    return ds


def _grdc_read(grdc_station_path, start, end):
    if not os.path.exists(grdc_station_path):
        raise ValueError("Data file ", grdc_station_path, " does not exist!")
    else:
        with open(
                grdc_station_path, 'r', encoding='utf-8',
                errors='ignore') as file:
            data = file.read()

    metadata = _grdc_metadata_reader(grdc_station_path, data)

    allLines = data.split('\n')
    for i, line in enumerate(allLines):
        if line.startswith('# DATA'):
            header = i + 1
            break

    # Import GRDC data into dataframe and modify dataframe format
    grdc_station_df = pd.read_csv(
        grdc_station_path,
        skiprows=header,
        delimiter=';',
        parse_dates=['YYYY-MM-DD'])
    grdc_station_df = grdc_station_df.rename(columns={
        'YYYY-MM-DD': 'time',
        ' Value': 'streamflow'
    })
    grdc_station_df = grdc_station_df.reset_index().set_index(
        pd.DatetimeIndex(grdc_station_df['time']))
    grdc_station_df = grdc_station_df.drop(columns=['hh:mm', 'index', 'time'])

    # Select GRDC station data that matches the forecast results Date
    grdc_station_select = grdc_station_df.loc[start:end]

    return metadata, grdc_station_select


def _grdc_metadata_reader(grdc_station_path, allLines):
    """
    # Initiating a dictionary that will contain all GRDC attributes.
    # This function is based on earlier work by Rolf Hut.
    # https://github.com/RolfHut/GRDC2NetCDF/blob/master/GRDC2NetCDF.py
    # DOI: 10.5281/zenodo.19695
    # that function was based on earlier work by Edwin Sutanudjaja
    # from Utrecht University.
    # https://github.com/edwinkost/discharge_analysis_IWMI
    # Modified by Susan Branchett
    """

    # initiating a dictionary that will contain all GRDC attributes:
    attributeGRDC = {}

    # split the content of the file into several lines
    allLines = allLines.replace("\r", "")
    allLines = allLines.split("\n")

    # get grdc ids (from files) and check their consistency with their
    # file names
    id_from_file_name = int(
        os.path.basename(grdc_station_path).split(".")[0].split("_")[0])
    id_from_grdc = None
    if id_from_file_name == int(allLines[8].split(":")[1].strip()):
        id_from_grdc = int(allLines[8].split(":")[1].strip())
    else:
        print("GRDC station " + str(id_from_file_name) + " (" +
              str(grdc_station_path) + ") is NOT used.")

    if id_from_grdc is not None:

        attributeGRDC["grdc_file_name"] = grdc_station_path
        attributeGRDC["id_from_grdc"] = id_from_grdc

        try:
            attributeGRDC["file_generation_date"] = \
                str(allLines[6].split(":")[1].strip())
        except:
            attributeGRDC["file_generation_date"] = "NA"

        try:
            attributeGRDC["river_name"] = \
                str(allLines[9].split(":")[1].strip())
        except:
            attributeGRDC["river_name"] = "NA"

        try:
            attributeGRDC["station_name"] = \
                str(allLines[10].split(":")[1].strip())
        except:
            attributeGRDC["station_name"] = "NA"

        try:
            attributeGRDC["country_code"] = \
                str(allLines[11].split(":")[1].strip())
        except:
            attributeGRDC["country_code"] = "NA"

        try:
            attributeGRDC["grdc_latitude_in_arc_degree"] = \
                float(allLines[12].split(":")[1].strip())
        except:
            attributeGRDC["grdc_latitude_in_arc_degree"] = "NA"

        try:
            attributeGRDC["grdc_longitude_in_arc_degree"] = \
                float(allLines[13].split(":")[1].strip())
        except:
            attributeGRDC["grdc_longitude_in_arc_degree"] = "NA"

        try:
            attributeGRDC["grdc_catchment_area_in_km2"] = \
                float(allLines[14].split(":")[1].strip())
            if attributeGRDC["grdc_catchment_area_in_km2"] <= 0.0:
                attributeGRDC["grdc_catchment_area_in_km2"] = "NA"
        except:
            attributeGRDC["grdc_catchment_area_in_km2"] = "NA"

        try:
            attributeGRDC["altitude_masl"] = \
                float(allLines[15].split(":")[1].strip())
        except:
            attributeGRDC["altitude_masl"] = "NA"

        try:
            attributeGRDC["dataSetContent"] = \
                str(allLines[20].split(":")[1].strip())
        except:
            attributeGRDC["dataSetContent"] = "NA"

        try:
            attributeGRDC["units"] = str(allLines[22].split(":")[1].strip())
        except:
            attributeGRDC["units"] = "NA"

        try:
            attributeGRDC["time_series"] = \
                str(allLines[23].split(":")[1].strip())
        except:
            attributeGRDC["time_series"] = "NA"

        try:
            attributeGRDC["no_of_years"] = \
                int(allLines[24].split(":")[1].strip())
        except:
            attributeGRDC["no_of_years"] = "NA"

        try:
            attributeGRDC["last_update"] = \
                str(allLines[25].split(":")[1].strip())
        except:
            attributeGRDC["last_update"] = "NA"

        try:
            attributeGRDC["nrMeasurements"] = \
                int(str(allLines[38].split(":")[1].strip()))
        except:
            attributeGRDC["nrMeasurements"] = "NA"

    return attributeGRDC
