from setuptools import setup

# Executable scripts obtained from the make target list_py_scripts
ENTRY_POINTS = {
    "console_scripts": [
        "djunct_calc_mont_dims.py=afni_python.djunct_calc_mont_dims:main",
        "djunct_combine_str.py=afni_python.djunct_combine_str:main",
        "djunct_select_str.py=afni_python.djunct_select_str:main",
        "DoPerRoi.py=afni_python.DoPerRoi:main",
        "abids_json_info.py=afni_python.abids_json_info:main",
        "abids_json_tool.py=afni_python.abids_json_tool:main",
        "abids_tool.py=afni_python.abids_tool:main",
        "afni_proc.py=afni_python.afni_proc:main",
        "afni_restproc.py=afni_python.afni_restproc:main",
        "afni_skeleton.py=afni_python.afni_skeleton:main",
        "afni_system_check.py=afni_python.afni_system_check:main",
        "afni_util.py=afni_python.afni_util:main",
        "align_epi_anat.py=afni_python.align_epi_anat:main",
        "apqc_make_html.py=afni_python.apqc_make_html:main",
        "apqc_make_tcsh.py=afni_python.apqc_make_tcsh:main",
        "auto_warp.py=afni_python.auto_warp:main",
        "BayesianGroupAna.py=afni_python.BayesianGroupAna:main",
        "demoExpt.py=afni_python.demoExpt:main",
        "eg_main_chrono.py=afni_python.eg_main_chrono:main",
        "fat_lat_csv.py=afni_python.fat_lat_csv:main",
        "fat_mat_sel.py=afni_python.fat_mat_sel:main",
        "fat_mvm_gridconv.py=afni_python.fat_mvm_gridconv:main",
        "fat_mvm_prep.py=afni_python.fat_mvm_prep:main",
        "fat_mvm_review.py=afni_python.fat_mvm_review:main",
        "fat_mvm_scripter.py=afni_python.fat_mvm_scripter:main",
        "fat_roi_row.py=afni_python.fat_roi_row:main",
        "gen_epi_review.py=afni_python.gen_epi_review:main",
        "gen_group_command.py=afni_python.gen_group_command:main",
        "gen_ss_review_scripts.py=afni_python.gen_ss_review_scripts:main",
        "gen_ss_review_table.py=afni_python.gen_ss_review_table:main",
        "lpc_align.py=afni_python.lpc_align:main",
        "make_pq_script.py=afni_python.make_pq_script:main",
        "make_random_timing.py=afni_python.make_random_timing:main",
        "make_stim_times.py=afni_python.make_stim_times:main",
        "meica.py=afni_python.meica:main",
        "neuro_deconvolve.py=afni_python.neuro_deconvolve:main",
        "parse_fs_lt_log.py=afni_python.parse_fs_lt_log:main",
        "python_module_test.py=afni_python.python_module_test:main",
        "quick.alpha.vals.py=afni_python.quick.alpha.vals:main",
        "read_matlab_files.py=afni_python.read_matlab_files:main",
        "realtime_receiver.py=afni_python.realtime_receiver:main",
        "RetroTS.py=afni_python.RetroTS:main",
        "slow_surf_clustsim.py=afni_python.slow_surf_clustsim:main",
        "tedana_wrapper.py=afni_python.tedana_wrapper:main",
        "timing_tool.py=afni_python.timing_tool:main",
        "uber_align_test.py=afni_python.uber_align_test:main",
        "uber_proc.py=afni_python.uber_proc:main",
        "uber_skel.py=afni_python.uber_skel:main",
        "uber_subject.py=afni_python.uber_subject:main",
        "uber_ttest.py=afni_python.uber_ttest:main",
        "unWarpEPI.py=afni_python.unWarpEPI:main",
        "xmat_tool.py=afni_python.xmat_tool:main",
    ]
}
SCRIPTS = [
    "scripts/1d_tool.py",
    "scripts/1dplot.py",
]


if __name__ == "__main__":
    setup(
        name="afni_python",
        version="0.0.1",
        description="AFNI python package, contained in src/python_scripts of the AFNI codebase",
        url="git+https://github.com/afni/afni.git",
        author="AFNI team",
        author_email="afni.bootcamp@gmail.com",
        license="GPL3",
        packages=["afni_python"],
        install_requires=["numpy", "matplotlib"],
        entry_points=ENTRY_POINTS,
        scripts=SCRIPTS,
        zip_safe=False,
    )
