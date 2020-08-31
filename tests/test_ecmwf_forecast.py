from datetime import datetime
from glob import glob
import os

from numpy.testing import assert_almost_equal, assert_array_equal
import pytest
import xarray as xr


from spt_compute import run_ecmwf_forecast_process

from .conftest import compare_warnings, RAPID_EXE_PATH, SetupECMWFForecast


@pytest.fixture(scope="function")
def ecmwf_setup(request, tclean):
    return SetupECMWFForecast(tclean, "dominican_republic-haina", "ecmwf")


@pytest.fixture(scope="function")
def ecmwf_setup_forcing(request, tclean):
    return SetupECMWFForecast(tclean, "dominican_republic-haina_forcing", "ecmwf", historical=False)


def test_ecmwf_forecast(ecmwf_setup):
    """
    Test basic ECMWF forecast process.
    """
    qout_names = [
        'Qout_dominican_republic_haina_5.nc',
        'Qout_dominican_republic_haina_50.nc',
        'Qout_dominican_republic_haina_51.nc',
        'Qout_dominican_republic_haina_52.nc',
    ]
    out_forecast_folder = '20170708.00'
    watershed = 'dominican_republic-haina'
    region = 'C.america'

    start_datetime = datetime.utcnow()
    run_ecmwf_forecast_process(rapid_executable_location=RAPID_EXE_PATH,
                               rapid_io_files_location=ecmwf_setup.rapid_io_folder,
                               ecmwf_forecast_location=ecmwf_setup.lsm_folder,
                               main_log_directory=ecmwf_setup.log_folder,
                               subprocess_log_directory=ecmwf_setup.subprocess_log_folder,
                               mp_execute_directory=ecmwf_setup.multiprocess_execute_folder,
                               region=region,
                               initialize_flows=True,
                               download_ecmwf=False,
                               mp_mode='multiprocess')

    output_folder = os.path.join(ecmwf_setup.rapid_io_folder, 'output', watershed, out_forecast_folder)
    # check log file exists
    log_files = glob(os.path.join(ecmwf_setup.log_folder,
                                  "spt_compute_ecmwf_{0:%y%m%d%H%M}*.log".format(start_datetime)))
    assert len(log_files) == 1
    # check Qout files
    for qout_name in qout_names:
        qout_file = os.path.join(output_folder, qout_name)
        assert os.path.exists(qout_file)
        compare_qout_file = os.path.join(ecmwf_setup.watershed_compare_folder,
                                         out_forecast_folder,
                                         qout_name)
        with xr.open_dataset(qout_file) as xqf, \
                xr.open_dataset(compare_qout_file) as xqc:
            assert_almost_equal(xqf.Qout.values, xqc.Qout.values)
            assert_array_equal(xqf.rivid.values, xqc.rivid.values)
            assert_almost_equal(xqf.lat.values, xqc.lat.values)
            assert_almost_equal(xqf.lon.values, xqc.lon.values)

    # check Qinit file
    assert os.path.exists(os.path.join(ecmwf_setup.watershed_input_folder, 'Qinit_20170708t00.csv'))


def test_ecmwf_forecast_historical(ecmwf_setup):
    """
    Test basic ECMWF forecast process.
    """
    qout_names = [
        'Qout_dominican_republic_haina_5.nc',
        'Qout_dominican_republic_haina_50.nc',
        'Qout_dominican_republic_haina_51.nc',
        'Qout_dominican_republic_haina_52.nc',
    ]
    out_forecast_folder = '20170708.00'
    watershed = 'dominican_republic-haina'
    region = 'C.america'

    start_datetime = datetime.utcnow()
    run_ecmwf_forecast_process(rapid_executable_location=RAPID_EXE_PATH,
                               rapid_io_files_location=ecmwf_setup.rapid_io_folder,
                               ecmwf_forecast_location=ecmwf_setup.lsm_folder,
                               era_interim_data_location=ecmwf_setup.historical_input_folder,
                               main_log_directory=ecmwf_setup.log_folder,
                               subprocess_log_directory=ecmwf_setup.subprocess_log_folder,
                               mp_execute_directory=ecmwf_setup.multiprocess_execute_folder,
                               region=region,
                               warning_flow_threshold=0.1,
                               initialize_flows=True,
                               create_warning_points=True,
                               download_ecmwf=False,
                               mp_mode='multiprocess')

    output_folder = os.path.join(ecmwf_setup.rapid_io_folder, 'output', watershed, out_forecast_folder)
    # check log file exists
    log_files = glob(os.path.join(ecmwf_setup.log_folder,
                                  "spt_compute_ecmwf_{0:%y%m%d%H%M}*.log".format(start_datetime)))
    assert len(log_files) == 1
    # check Qout files
    for qout_name in qout_names:
        qout_file = os.path.join(output_folder, qout_name)
        assert os.path.exists(qout_file)

        compare_qout_name = os.path.splitext(qout_name)[0] + "_init.nc"
        compare_qout_file = os.path.join(ecmwf_setup.watershed_compare_folder,
                                         out_forecast_folder,
                                         compare_qout_name)
        with xr.open_dataset(qout_file) as xqf, \
                xr.open_dataset(compare_qout_file) as xqc:
            assert_almost_equal(xqf.Qout.values, xqc.Qout.values)
            assert_array_equal(xqf.rivid.values, xqc.rivid.values)
            assert_almost_equal(xqf.lat.values, xqc.lat.values)
            assert_almost_equal(xqf.lon.values, xqc.lon.values)

    # check Qinit file
    assert os.path.exists(os.path.join(ecmwf_setup.watershed_input_folder, 'Qinit_20170708t00.csv'))

    # check warning points
    return_2_warnings = os.path.join(output_folder, "return_2_points.geojson")
    return_10_warnings = os.path.join(output_folder, "return_10_points.geojson")
    return_20_warnings = os.path.join(output_folder, "return_20_points.geojson")
    assert os.path.exists(return_2_warnings)
    compare_return2_file = os.path.join(ecmwf_setup.watershed_compare_folder,
                                        out_forecast_folder,
                                        'return_2_points.geojson')

    compare_warnings(return_2_warnings, compare_return2_file)
    assert os.path.exists(return_10_warnings)
    compare_return10_file = os.path.join(ecmwf_setup.watershed_compare_folder,
                                        out_forecast_folder,
                                        'return_10_points.geojson')
    compare_warnings(return_10_warnings, compare_return10_file)
    assert os.path.exists(return_20_warnings)
    compare_return20_file = os.path.join(ecmwf_setup.watershed_compare_folder,
                                        out_forecast_folder,
                                        'return_20_points.geojson')
    compare_warnings(return_20_warnings, compare_return20_file)


def test_ecmwf_forecast_forcing(ecmwf_setup_forcing):
    """
    Test basic ECMWF forecast process with forcing data.
    """
    qout_names = [
        'Qout_dominican_republic_haina_forcing_5.nc',
        'Qout_dominican_republic_haina_forcing_50.nc',
        'Qout_dominican_republic_haina_forcing_51.nc',
        'Qout_dominican_republic_haina_forcing_52.nc',
    ]
    out_forecast_folder = '20170708.00'
    watershed = 'dominican_republic-haina_forcing'
    region = 'C.america'

    start_datetime = datetime.utcnow()
    run_ecmwf_forecast_process(rapid_executable_location=RAPID_EXE_PATH,
                               rapid_io_files_location=ecmwf_setup_forcing.rapid_io_folder,
                               ecmwf_forecast_location=ecmwf_setup_forcing.lsm_folder,
                               main_log_directory=ecmwf_setup_forcing.log_folder,
                               subprocess_log_directory=ecmwf_setup_forcing.subprocess_log_folder,
                               mp_execute_directory=ecmwf_setup_forcing.multiprocess_execute_folder,
                               region=region,
                               warning_flow_threshold=0.1,
                               initialize_flows=True,
                               create_warning_points=True,
                               download_ecmwf=False,
                               mp_mode='multiprocess')

    output_folder = os.path.join(ecmwf_setup_forcing.rapid_io_folder, 'output', watershed, out_forecast_folder)
    # check log file exists
    log_files = glob(os.path.join(ecmwf_setup_forcing.log_folder,
                                  "spt_compute_ecmwf_{0:%y%m%d%H%M}*.log".format(start_datetime)))
    assert len(log_files) == 1
    # check Qout files
    for qout_name in qout_names:
        qout_file = os.path.join(output_folder, qout_name)
        assert os.path.exists(qout_file)
        compare_qout_file = os.path.join(ecmwf_setup_forcing.watershed_compare_folder,
                                         out_forecast_folder,
                                         qout_name)
        with xr.open_dataset(qout_file) as xqf, \
                xr.open_dataset(compare_qout_file) as xqc:
            assert_almost_equal(xqf.Qout.values, xqc.Qout.values)
            assert_array_equal(xqf.rivid.values, xqc.rivid.values)
            assert_almost_equal(xqf.lat.values, xqc.lat.values)
            assert_almost_equal(xqf.lon.values, xqc.lon.values)

    # check Qinit file
    assert os.path.exists(os.path.join(ecmwf_setup_forcing.watershed_input_folder, 'Qinit_20170708t00.csv'))
