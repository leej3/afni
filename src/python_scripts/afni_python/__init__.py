from pathlib import Path

known_py2 = [
    "afni_restproc.py",
    "afni_skeleton.py",
    "afni_xmat.py",
    "DoPerRoi.py",
    "eg_main_chrono.py",
    "fat_mat_sel.py",
    "fat_mvm_gridconv.py",
    "fat_mvm_prep.py",
    "fat_mvm_review.py",
    "fat_mvm_scripter.py",
    "fat_roi_row.py",
    "gui_uber_skel.py",
    "gui_uber_proc.py",
    "gui_xmat.py",
    "lib_dti_sundry.py",
    "lib_fat_funcs.py",
    "lib_fat_plot_sel.py",
    "lib_surf_clustsim.py",
    "lib_uber_align.py",
    "lib_uber_skel.py",
    "lpc_align.py",
    "make_pq_script.py",
    "make_stim_times.py",
    "meica.py",
    "neuro_deconvolve.py",
    "parse_fs_lt_log.py",
    "python_module_test.py",
    "quick.alpha.vals.py",
    "read_matlab_files.py",
    "RetroTS.py",  # requires scipy
    "slow_surf_clustsim.py",
    "uber_align_test.py",
    "uber_proc.py",
    "uber_skel.py",
    "ui_xmat.py",
    "unWarpEPI.py",
    "xmat_tool.py",
    "gui_uber_ttest.py",
    "gui_uber_align_test.py",
    "lib_qt_gui.py",
    "gui_uber_subj.py",
    "demoExpt.py",
    "gui_xmat.py",  # wx required
    "lib_matplot.py",  # wx required
    "lib_RR_plot.py",  # wx required
    "lib_wx.py",  # wx required
]

not_importable = [
    "abids_lib.py",
    "abids_json_tool.py",
    "ClustExp_HistTable.py",
    "quick.alpha.vals.py",
    "abids_json_info.py",
    "tedana_wrapper.py",
    "BayesianGroupAna.py",
    "abids_tool.py",
    "ClustExp_StatParse.py",
]

other_problems = [
    # requires rpy2 with py2. need a rewrite
    "lib_fat_Rfactor.py",
    "fat_lat_csv.py",
    "__init__.py",
    "lib_system_check.py",
    "afni_system_check.py",
    "djunct_is_label.py",
    "1d_tool.py",
    "1dplot.py",
]

do_not_import = known_py2 + not_importable + other_problems

__all__ = [
    f.stem for f in Path(__file__).parent.glob("*.py") if f.name not in do_not_import
]

from afni_python import *
