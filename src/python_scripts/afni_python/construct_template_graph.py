#!/usr/bin/env python
# -*- coding: utf-8 -*-

import afni_python.afni_base as ab

from afni_python.pipeline_utils import (
    ShellComFuture, run_check_afni_cmd, prepare_afni_output, make_nii_compatible)
from pathlib import Path
import glob
import os
import time
import shutil
from collections import OrderedDict


def align_centers(ps, dset=None, basedset=None, suffix="_ac"):
    """
    align the center of a dataset to the center of another
    dataset like a template
    """

    o = prepare_afni_output(dset, suffix,basepath='')
    # use shift transformation of centers between grids as initial
    # transformation. @Align_Centers (3drefit)
    basedset_path = basedset.ppve()

    if ps.do_center == 0:
        raise ValueError("This part of the pipeline needs to be checked")
        cmd_str = "@Align_Centers -base {basedset_path} -dset {dset.initname} -no_cp"
    else:
        cmd_str = "3dcopy %s %s" % (dset.initname, o.initname)
    cmd_str = cmd_str.format(**locals())

    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o})
    return out_dict['dset_1']


def automask(ps, dset=None, suffix="_am"):
    """
    automask - make simple mask
    """
    o = prepare_afni_output(dset, suffix)
    cmd_str = "3dAutomask -dilate 3 -apply_prefix %s %s" %     \
        (o.initname, dset.initname)
    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o})

    return out_dict['dset_1']


def skullstrip(ps, dset=None, suffix="_ns"):
    if(ps.do_skullstrip == 0):
        return dset

    o = prepare_afni_output(dset, suffix)
    cmd_str = "3dSkullStrip -prefix %s -input %s -push_to_edge" %     \
        (o.initname, dset.initname)
    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o})
    return out_dict['dset_1']


def unifize(ps, dset=None, suffix="_un"):
    """
    unifize - bias-correct a dataset
    """
    if(ps.do_unifize == 0):
        return dset
    o = prepare_afni_output(dset, suffix)
    cmd_str = "3dUnifize -gm -clfrac 0.4 -Urad 30 -prefix %s -input %s" %     \
        (o.initname, dset.initname)
    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o})
    return out_dict['dset_1']


@make_nii_compatible(
    mod_params={'args_in': [0, 1], 'ret_vals': [0]}, config_name='ps')
def rigid_align(dset, base, ps=None, suffix="_4rigid"):
    if any("NIFTI" == d.type for d in [dset, base]):
        err = "Function requires BRIK file. Try using make_nii_compatible."
        raise ValueError(err)
    if(ps.do_rigid == 0):
        return dset
    if base.view == '':
        o = prepare_afni_output(dset, suffix, view='+orig')
    else:
        o = prepare_afni_output(dset, suffix, view=base.view)

    chdir = str(Path(o.ppve()).parent)
    # This step is challenging because auto_tlrc fails silently if it is not
    # provided with an input dataset in the "current directory" This means fn
    # and bn are used without a relative dir spec. Also the chdir key value
    # pair is used for the dictionary passed to run_check_afni_cmd
    input_name = dset.fn
    outname = o.fn
    base_in = base.ppve()
    # remove temp
    outaff_glob = "{f}.HEAD {f}.BRIK* {f}.nii*"
    outaff_glob = outaff_glob.format(f=o.bn + o.view)
    out_prefix = o.bn
    # compute registration alignment to the base template
    # but apply only the rigid component and put into
    # grid of base template
    cmd_str = """\
    @auto_tlrc -base {base_in} -input {input_name} -no_ss \
    -rigid_equiv -suffix {suffix} -pad_input 15 -OK_maxite -maxite 50 \
     && \
    rm {outaff_glob}; \
    3dAllineate -1Dmatrix_apply {out_prefix}.Xat.rigid.1D \
    -master {base_in} -prefix {outname}  \
    -input {input_name}
    """
    cmd_str = cmd_str.format(**locals())

    # mat_exists = os.path.exists("%s_mat.aff12.1D" % (o.initpath + o.bn))
    # outaff_prefix = "%s_temp%s" % (dset.out_prefix(), suffix)
#    cmd_str = """\
#    align_epi_anat.py -dset1 {input_name} -dset2 {base_in} \
#    -dset1_strip None -dset2_strip None \
#    -giant_move -ok_to_exist -suffix _temp{suffix} {rewrite} && \
#    -P > {out_prefix}_mat.aff12.1D && \
#    cat_matvec {outaff_prefix}_mat.aff12.1D \
#    3dAllineate -1Dmatrix_apply {out_prefix}_mat.aff12.1D \
#    -master {base_in} -prefix {out_prefix}  \
#    -input {input_name} {rewrite}
#    """
    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o, 'chdir': chdir})
    return out_dict['dset_1']


@make_nii_compatible(
    mod_params={'args_in': [0, 1], 'ret_vals': [0]}, config_name='ps')
def affine_align(dset, base, suffix="_aff", aff_type="affine", ps=None):
    assert(dset is not None)
    if any("NIFTI" == d.type for d in [dset, base]):
        err = "Function requires BRIK file. Try using make_nii_compatible."
        raise ValueError(err)

    if base.view == '':
        o = prepare_afni_output(dset, suffix, view='+orig')
    else:
        o = prepare_afni_output(dset, suffix, view=base.view)

    chdir = str(Path(o.ppve()).parent)
    input_name = dset.fn
    out_prefix = o.bn
    mat_exists = os.path.exists("%s_mat.aff12.1D" % out_prefix)
    base_in = base.ppve()
    # won't use affine output if rigid only is requested
    outaff_prefix = "%s_temp%s" % (dset.bn, suffix)
    outaff_name = "{p}".format(p=o.bn + o.view)
    # compute registration alignment to the base template
    # but apply only the rigid component and put into
    # grid of base template
    if(aff_type == "rigid"):
        rigid_opt = "-rigid_equiv"
    else:
        rigid_opt = ""

    cmd_str = """\
    @auto_tlrc -base {base_in} -input {input_name} -no_ss -onewarp\
    {rigid_opt} -suffix {suffix} -pad_input 15 -OK_maxite -maxite 50 \
    """

#    cmd_str = """\
#    align_epi_anat.py -dset1 {input_name} -dset2 {base_in} \
#    -dset1_strip None -dset2_strip None \
#    -giant_move -ok_to_exist -suffix _temp{suffix} {rewrite} && \
#    cat_matvec {outaff_prefix}_mat.aff12.1D \
#    -P > {out_prefix}_mat.aff12.1D && \
#    3dAllineate -1Dmatrix_apply {out_prefix}_mat.aff12.1D \
#    -master {base_in} -prefix {out_prefix}  \
#    -input {input_name} {rewrite}
#    """
    cmd_str = cmd_str.format(**locals())

    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o, 'chdir': chdir},
        "** ERROR: Could not align using")
    o = out_dict['dset_1']

    # may only want just rigid, so just apply warp and delete the affine
    # output
    if aff_type == 'rigid':
        cmd_str = """\
           rm {outaff_name}; \
           3dAllineate -1Dmatrix_apply {out_prefix}.Xat.rigid.1D \
           -master {base_in} -prefix {out_prefix}  \
           -input {input_name}
           """
        out_dict = run_check_afni_cmd(
            cmd_str, ps, {'dset_1': o, 'chdir': chdir},
            "** ERROR: Could not align rigidly using")
        o = out_dict[dset]

    return o


def aniso_smooth(ps, dset=None, suffix="_as", iters="1"):
    """
    anisotropically smooth data
    """
    print("anisosmooth %s" % dset.out_prefix())
    if(ps.do_anisosmooth == 0):
        return dset
    if(dset.type == 'NIFTI'):
        # copy original to a temporary file
        print("dataset input name is %s" % dset.input())
        ao = ab.strip_extension(dset.input(), ['.nii', 'nii.gz'])
        print("new AFNI name is %s" % ao[0])
        aao = ab.afni_name("%s" % (ao[0]))
        aao.to_afni(new_view="+orig")
        o = ab.afni_name("%s%s%s" % (aao.out_prefix(), suffix, aao.view))
    else:
        o = dset.new("%s%s" % (dset.out_prefix(), suffix))
    cmd_str = "3danisosmooth -3D -iters %s -noneg -prefix %s -mask %s %s" %     \
        (iters, o.out_prefix(), dset.input(), dset.input())
    print("executing:\n %s" % cmd_str)
    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o}, "** ERROR: Could not anisotropically smooth using")
    o = out_dict['dset_1']

    return o


def upsample_dset(ps, dset=None, suffix="_rs"):
    """
    upsample a dataset to double its resolution - 8x number of voxels in 3D
    resample data 2x (1/2 the voxel size)
    """

    print("upsample %s" % dset.out_prefix())
    if(not(ps.upsample_level)):
        return dset
    if(dset.type == 'NIFTI'):
        # copy original to a temporary file
        print("dataset input name is %s" % dset.input())
        ao = ab.strip_extension(dset.input(), ['.nii', 'nii.gz'])
        print("new AFNI name is %s" % ao[0])
        aao = ab.afni_name("%s" % (ao[0]))
        aao.to_afni(new_view="+orig")
        o = ab.afni_name("%s%s%s" % (aao.out_prefix(), suffix, aao.view))
    else:
        o = dset.new("%s%s" % (dset.out_prefix(), suffix))

    min_d = min_dim_dset(ps, dset)
    min_d = min_d / 2.0

    cmd_str = "3dresample -dxyz %s %s %s -prefix %s -input %s" %     \
        (min_d, min_d, min_d, o.out_prefix(), dset.input())
    print("executing:\n %s" % cmd_str)
    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o}, "** ERROR: Could not upsample using")
    o = out_dict['dset_1']

    return o


def resample_dset(ps, dset, base, suffix="_rs"):
    """
    resample a dataset to grid of another dataset
    """
    print("resample %s" % dset.out_prefix())
    try:
        os.chdir(dset.path)
    except:
        os.chdir(os.path.abspath(os.path.dirname(dset)))
    assert(dset is not None)
    if(dset.type == 'NIFTI'):
        # copy original to a temporary file
        print("dataset input name is %s" % dset.input())
        ao = ab.strip_extension(dset.input(), ['.nii', 'nii.gz'])
        print("new AFNI name is %s" % ao[0])
        aao = ab.afni_name("%s" % (ao[0]))
        aao.to_afni(new_view="+orig")
        o = ab.afni_name("%s%s%s" % (aao.out_prefix(), suffix, aao.view))
    else:
        o = dset.new("%s%s" % (dset.out_prefix(), suffix))

    base_in = base.input()
    out_prefix = o.out_prefix()
    input_name = dset.input()

    cmd_str = "\
        3dresample -master %s -prefix %s \
        -input %s \
        " % (base_in, out_prefix, input_name)
    print("executing:\n %s" % cmd_str)
    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o}, "** ERROR: Could not resample using")
    o = out_dict['dset_1']

    return o


def min_dim_dset(ps, dset=None):
    """
    find smallest dimension of dataset in x,y,z
    """
    cmd_str = "3dAttribute DELTA %s" % dset.ppve()
    shell_obj = ShellComFuture(cmd_str, eo=ps.oexec, default_text="1 0 -1")
    out_dict = run_check_afni_cmd(cmd_str, ps, {'shell_obj': shell_obj},
                                  "** ERROR: Could not get dimension attribute using")

    out_shell_obj = out_dict['shell_obj']
    min_dx = min([abs(float(x)) for x in out_shell_obj.future_text(0).split()])

    if(min_dx == 0.0):
        min_dx = 1.0
    return min_dx


def get_mean_brain(dset_list, ps, dset_glob, suffix="_rigid", preprefix=""):
    """
    compute mean and standard deviation across a group of datasets
    """
    assert(dset_list[0] is not None)
    file_ending = dset_list[0].view + dset_list[0].extension
    o = dset_list[0].new("%smean%s%s" % (preprefix, suffix, file_ending))
    cmd_str = """\
    3dMean -prefix {o.initname}  {dset_glob}; \
    3dMean -stdev -prefix {preprefix}stdev{suffix}{file_ending} {dset_glob}
    """
    cmd_str = cmd_str.format(**locals())

    out_dict = run_check_afni_cmd(
        cmd_str, ps, {'dset_1': o}, "** ERROR: Could not compute mean using")

    return out_dict['dset_1']


def get_typical_brain(dists_brains, ps, suffix="_nl", preprefix="typical_"):
    """
    compute typical subjects from across a group of datasets given
    tuple list of distances and subject brains
    distances calculated before, in another function
    """
    assert(dists_brains[0][0] is not None)

    # sort the distances with their corresponding subject brain datasets
    sdist = sorted(dists_brains, key=itemgetter(0))
    typ_brain = sdist[0][1]
    typ_brain_input = typ_brain.ppv()
    print("typical brain is %s with distance %f" %
          (typ_brain.prefix, sdist[0][0]))

    print("cd %s" % ps.odir)
    if(not ps.dry_run()):
        os.chdir(ps.odir)

    o = ab.afni_name("%ssubject%s" % (preprefix, suffix))
    o.path = ps.odir
    o.view = typ_brain.view
    output_prefix = o.ppv()

    cmd_str = """\
    3dcopy {typ_brain_input} {output_prefix}
    """
    cmd_str = cmd_str.format(**locals())
    print("executing:\n %s" % cmd_str)

    out_dict = run_check_afni_cmd(cmd_str, ps, {
                                  'dset_1': o}, "** ERROR: Could not copy typical subject to mean template directory using")
    o = out_dict['dset_1']

    return o


def get_rigid_mean(ps, basedset, dsetlist, delayed):
    """
    first iteration - compute rigid mean across all subjects
    """

    aligned_brains = []

    #  these functions are delayed using the function wrapper "delayed" from
    #  dask to help with parallel execution
    for dset in dsetlist:
        # start off just aligning the centers of the datasets
        aname = delayed(align_centers)(ps, dset=dset, basedset=basedset)
        amname = delayed(skullstrip)(ps, dset=aname)
        dname = delayed(unifize)(ps, dset=amname)
        af_aligned = delayed(rigid_align)(
            dname, basedset, ps=ps, suffix="_4rigid")
        # change back to original directory
        # af_aligned_cd = delayed(change_dirs)(af_aligned,ps, path=cwd)

        #  We can continue our python session. Whenever we query the affine
        # object we will be informed of its status.
        aligned_brains.append(af_aligned)

    file_ending = dsetlist[0].view + dsetlist[0].extension
    rigid_mean_brain = delayed(get_mean_brain)(
        aligned_brains,
        ps,
        dset_glob="*_4rigid" + file_ending,
        suffix="_rigid", preprefix="tp0_")

    print("Configured first processing loop")

    # return the rigid mean brain template and the rigidly aligned_brains
    return (rigid_mean_brain, aligned_brains)


def get_affine_mean(ps, basedset, dsetlist, delayed):
    """
    2nd iteration - compute affine mean across all subjects
    """
    aligned_brains = []

    # this time, we don't need to do all the other steps again
    #  if we're using the stripped, unifized
    for dset in dsetlist:
        af_aligned = delayed(affine_align)(dset, basedset, suffix="_affx",
                                           ps=ps)
        #  We can continue our python session. Whenever we query the affine
        # object we will be informed of its status.
        aligned_brains.append(af_aligned)

    file_ending = dsetlist[0].view + dsetlist[0].extension
    affine_mean_brain = delayed(get_mean_brain)(
        aligned_brains,
        ps,
        dset_glob="*/*_affx" + file_ending,
        suffix="_affx", preprefix="tp1_")

    print("Configured first processing loop")
    # return the rigid mean brain template and the rigidly aligned_brains
    # Dask can't return two separate objects, so combine into a single tuple
    return (affine_mean_brain, aligned_brains)


def nl_align(ps, dset, base, iniwarpset, **kwargs):
    """
    nonlinearly align dataset to a base dataset
    initial warp provided by either iniwarpset as an AFNI dataset
    or by iniwarplevel and composed by name dset_nlx_WARP+tlrc
    with x as a digit string here (0,1,2,3)
    returns warped dataset and WARP dataset of deformation distances
    """
    # parse the keyword arguments
    suffix = kwargs['suffix']
    # the initial level of warp neighborhoods
    inilev = kwargs['inilev']

    # an index for initial warps in previously saved datasets (0-4)
    # these aren't the same as the intermediate level datasets below
    # and the level will not match the "inilev" below. J

    iniwarplevel = kwargs.get('iniwarplevel',[])
    upsample = kwargs['upsample']
    qw_opts = kwargs['qw_opts']

    # does the OMP_NUM_THREAD variable propagate to workers?s
    # show current setting for OpenMP
    ps.report_omp()

    # create output dataset structure
    o = prepare_afni_output(dset, suffix)
    o.rps = str(Path(o.initname).parent)
    # make warp dataset structure too
    warpset = prepare_afni_output(o, "WARP")
    input_name = dset.initname
    out_prefix = str(Path(o.rps) / o.bn)
    out_file = str(Path(o.rps) / o.fn)
    base_in = base.ppve()
    # may want to check for typical subject processing here
    #  if(base_in == dset.input
    # but we may also want to keep a copy of the subject as the typical subject
    # in the parent directory for reference or both

    # add check for reusing a warp from a previous trial of the *same* Qwarp
    # that was aborted either by the cluster or by a "nanny" process
    # previous output has the form
    #   {o.out_prefix}_Lev0.0193x0232x0200_WARPsave+tlrc.HEAD
    #   {o.out_prefix}_Lev1.0145x0173x0149_WARPsave+tlrc.HEAD
    # look for last {o.out_prefix}_Levn.*_WARPsave+tlrc.HEAD
    #  if it exists, make it iniwarpset instead of existing iniwarpset
    # and set -inilev to start with 1 more than that level
    wll = ("11", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1", "0")
    # check warps from last to first to see if any already exist
    #  use existing warps to restart interrupted warp
    iwset = None
    ilev_opt = None
    # see if there are any intermediate warps saved on the disk
    file_ending = o.view + o.extension
    wlg = glob.glob("%s_Lev*.*_WARPsave" % o.pp() + file_ending)
    # search for highest Level number warp
    for wl in wlg:
        print("Found warp named %s" % wl)
        for iwl in wll:
            if (iwl in wl):
                print("%s matches file %s" % (iwl, wl))
                iwset = prepare_afni_output(dset, suffix, view=base.view)
                iwset.prefix = str.split(os.path.splitext(
                    os.path.basename(wl))[0], "+tlrc")[0]
                inilev = int(iwl) + 1
                break
        if(iwset):  # found one, so stop looking and use this warp
            iniwarpset = iwset
            break

    # initial neighborhood level of warping to start with
    # determined either by kwargs or by previous intermediate warps
    # on restart+1
    ilev_opt = "-inilev %s" % inilev

    # if warp dataset provided here (either passed through or from previous intermediate save), use it
    if iniwarpset:
        iniwarp = "-iniwarp %s" % iniwarpset.input()
    else:
        # if just a level is provided for the initial warp, compose the name here
        if(iniwarplevel):
            # provide name of warp dataset
            iniwarpset = dset.new("%s_nl%s_WARP" %
                                  (dset.out_prefix(), iniwarplevel))
            iniwarp = "-iniwarp %s_nl%s_WARP+tlrc" % (
                dset.out_prefix(), iniwarplevel)
        # otherwise, no initial warp given, so skip the initial warp for 3dQwarp
        # this should only happen at nl 0
        else:
            iniwarp = ""


    # call AFNI's nonlinear alignment and then delete the intermediate results
    # those will be used on system errors and nanny restarts
    cmd_str = """\
    3dQwarp -base {base_in} -source {input_name} \
    -prefix {out_file} {ilev_opt} {qw_opts} -saveall \
    {iniwarp}; \
    \\rm -f {out_prefix}*_WARPsave+tlrc.*
    """

    cmd_str = cmd_str.format(**locals())

    # check if output dataset was created
    out_dict = run_check_afni_cmd(
        cmd_str, ps, {"dset_1": o}, "Could not nonlinearly align using")
    o = out_dict['dset_1']
    return {'aa_brain': o, 'warp': warpset}


def resize_warp(ps, warp, rsz_brain, suffix="_rsz"):
    """
    resize warp deformation dataset by concatenating affine matrix
    help for 3dNwarpCat shows this order for its use with
    first an auto_tlrc affine alignment followed by a nonlinear warp with 3dQwarp
    Since we are doing the opposite order, we can reverse the order here
    3dNwarpCat -prefix Fred_total_WARP -warp1 Fred_WARP+tlrc.HEAD -warp2 Fred.Xat.1D

    3dNwarpCat -prefix Fred_total_WARP -warp2 Fred_WARP+tlrc.HEAD -warp1 Fred.Xat.1D

    Note, this like 3dNwarpCalc's nonlinear warp concatenation assume the same grid
    and center for the combination of the affine with nonlinear warps
    Because we have aligned centers first, this works.
    """

    # Use 3dNwarpApply for distant warps
    # create output dataset structure
    rsz_warp = prepare_afni_output(warp, suffix)

    aff_matrix = "%s.Xaff12.1D" % rsz_brain.rbn

    input_name = warp.initname
    out_file = rsz_warp.initname

    cmd_str = """\
    3dNwarpCat -prefix {out_file} -warp2 {input_name} -warp1 {aff_matrix}
    """
    cmd_str = cmd_str.format(**locals())

    # check if output dataset was created
    rsz_warp = run_check_afni_cmd(cmd_str, ps, {'dset_1': rsz_warp},
                                  "Could not resize warp using")

    return rsz_warp


def upsample_subjects_bases(ps, delayed, target_brain, aa_brains,
                            warpsetlist, resize_brain, **kwargs):
    """
    upsample all subjects, current base template resize base and warps
    """

    # upsample the mean target template
    target_brain = delayed(upsample_dset)(ps, dset=target_brain, suffix="_us")

    # make all the others match that newly upsampled target,
    # starting with the resize template (using resample)
    resize_brain = delayed(resample_dset)(
        ps, resize_brain, target_brain, suffix="_us")

    # need at least an empty matching list of warps as input
    if not warpsetlist:
        warpsetlist = [''] * len(aa_brains)

    # initialize the list of output brains and warps
    aa_brains_out = []
    warpsetlist_out = []

    # upsample all the affine brains and the warps
    for (aa_brain, warp) in zip(aa_brains, warpsetlist):
        # resample the affine brain
        aa_brain_out = delayed(resample_dset)(
            ps, aa_brain, target_brain, suffix="_us")

        # resample the warp
        warp_out = delayed(resample_dset)(
            ps, warp, target_brain, suffix="_us")

        # add the outputs to the list
        aa_brains_out.append(aa_brain_out)
        warpsetlist_out.append(warp_out)

    # return upsampled versions of
    #   mean brain, resize mean, affine_brains, warps
    return {'mean_brain_us': target_brain, 'resize_brain_us': resize_brain,
            'aa_brains_us': aa_brains_out,
            'warpsetlist_us': warpsetlist_out}


def compute_deformation_dist(ps, aa_brain, warp, suffix="_defdist"):
    """
    find mean deformation distance in deformation maps masked by original brain
    """
    # create output dataset structure
    o = prepare_afni_output(aa_brain, suffix)

    warp_name = warp.pv()
    out_prefix = o.out_prefix()
    # inverse warp to compute distance in affine space (before nonlinear warp)
    inv_warp = prepare_afni_output(warp, "_inv")
    inv_warp_prefix = inv_warp.out_prefix()
    inv_warp_name = inv_warp.pv()

    if ps.rewrite:
        rewrite = " -overwrite "
    else:
        rewrite = ""

    cmd_str = """\
    3dNwarpCat -warp1 \'INV({warp_name})\' -prefix {inv_warp_prefix} \
    {rewrite}
    """
    cmd_str = cmd_str.format(**locals())
    # check if inverse warp output dataset was created
    inv_warp = run_check_afni_cmd(cmd_str, ps, {'dset_1': inv_warp},
                                  "Could not compute inverse warp using")

    # fill holes in brain
    filled_brain = prepare_afni_output(aa_brain, "_filled")
    input_name = aa_brain.pv()
    filled_brain_name = filled_brain.pv()
    filled_brain_prefix = filled_brain.out_prefix()

    # fill holes to account for ventricles and such
    cmd_str = """\
    3dmask_tool -fill_holes  \
    -prefix {filled_brain_prefix} -inputs {input_name} \
    {rewrite}
    """

    cmd_str = cmd_str.format(**locals())

    # check if output dataset was created
    filled_brain = run_check_afni_cmd(cmd_str, ps, {'dset_1': filled_brain},
                                      "Could not fill holes using")

    zp_inv_warp = prepare_afni_output(warp, "_inv_zp")
    zp_inv_warp_prefix = zp_inv_warp.out_prefix()
    zp_inv_warp_name = zp_inv_warp.pv()

    if ps.rewrite:
        rewrite = " -overwrite "
    else:
        rewrite = ""

    cmd_str = """\
    3dZeropad -master {filled_brain_name} -prefix {zp_inv_warp_prefix} \
    {rewrite} {inv_warp_name}
    """
    cmd_str = cmd_str.format(**locals())
    # check if inverse warp output dataset was created
    zp_inv_warp = run_check_afni_cmd(cmd_str, ps, {'dset_1': zp_inv_warp},
                                     "Could not zeropad inverse warp using")

    # compute deformation distance at every voxel (3dcalc is another way,
    #   but with mask option especially,this should be a little faster)
    cmd_str = """\
    3dTstat -mask {filled_brain_name} -l2norm  \
    -prefix {out_prefix} \
    {rewrite}  {zp_inv_warp_name}
    """

    cmd_str = cmd_str.format(**locals())

    # check if output dataset was created
    o = run_check_afni_cmd(cmd_str, ps, {'dset_1': o},
                           "Could not compute deformation distance using")
    dist_prefix = o.ppv()

    # compute mean distance
    input_name = filled_brain.ppv()

    cmd_str = """\
    3dBrickStat -mask {input_name} -mean {dist_prefix}
    """
    cmd_str = cmd_str.format(**locals())
    shell_obj = ShellComFuture(cmd_str, eo=ps.oexec, default_text="1 0 -1")
    out_dict = run_check_afni_cmd(cmd_str, ps, {'shell_obj': shell_obj},
                                  "** ERROR: Could not get dimension attribute using")
    print("Running :\n%s" % cmd_str)
    out_dict = run_check_afni_cmd(cmd_str, ps, {'text_1': text_future},
                                  "** ERROR: Could not find minimum deformation using", chdir=o.path)

    out_shell_obj = out_dict['shell_obj']
    dist = float(out_shell_obj.future_text(0, 0))

    return(dist)


def itemgetter(*items):
    if len(items) == 1:
        item = items[0]

        def g(obj):
            return obj[item]
    else:
        def g(obj):
            return tuple(obj[item] for item in items)
    return g


def find_typical_subject(ps, delayed, aa_brains,
                         warpsetlist, **kwargs):
    """
    find typical subject, i.e. one with the lowest deformation distance
    given a list of subjects and a list of deformation maps-dx,dy,dz
    """

    # need at least an empty matching list of warps as input
    if not warpsetlist:
        warpsetlist = [''] * len(aa_brains)
        print("no warp list provided to find typical subject. This should never happen")
        return []

    # initialize the list of output distances and brains
    dists_brains = []

    # compute deformation distance for all the affine brains and the warps
    for (aa_brain, warp) in zip(aa_brains, warpsetlist):
        # compute distance
        aa_dist = delayed(compute_deformation_dist)(
            ps, aa_brain, warp, suffix="_defdist")

        # add the outputs to the list as a list of tuples of distance and brains
        dists_brains.append((aa_dist, aa_brain))
    # sort distances to find typical brain and make copy
    typ_brain = delayed(get_typical_brain)(
        dists_brains,
        ps)

    # return subject brain with shortest distance
    return(typ_brain)


def get_glob_pattern(dset,suffix):
    file_ending = dset.view + dset.extension
    rps = Path(dset.initname).parent / ("*%s"%suffix)
    return str(rps) + file_ending

def get_nl_leveln(ps, delayed, target_brain, aa_brains, warpsetlist, resize_brain, **kwargs):
    """
    find mean brain through nonlinear warping to an initial template (the previous mean brain)
    """

    if not warpsetlist:
        warpsetlist = [''] * len(aa_brains)
    nl_level = kwargs["nl_level"]
    tp_level = nl_level + 2
    preprefix = "tp%s_" % tp_level
    aa_brains_out = []
    warpsetlist_out = []
    # af_aligned, nlwarp_out
    for (aa_brain, warp) in zip(aa_brains, warpsetlist):
        brain_and_warp = delayed(nl_align)(
            ps, aa_brain, target_brain, warp, **kwargs)
        aa_brains_out.append(brain_and_warp['aa_brain'])
        warpsetlist_out.append(brain_and_warp['warp'])



    glob_pattern = delayed(get_glob_pattern)(aa_brains[0], kwargs['suffix'])
    nl_mean_brain = delayed(get_mean_brain)(
        aa_brains_out,
        ps,
        dset_glob=glob_pattern,
        suffix=kwargs['suffix'], preprefix=preprefix)

    # adjust size to avoid dilation and to match group
    # trying this out, Bob's 3dNwarpAdjust mostly works too. Could do affine at just last step.
    # may want more specialized function here instead - no shears,...
    nl_mean_brain = delayed(affine_align)(nl_mean_brain, resize_brain,
                                          suffix="_rsz", aff_type="affine",
                                          ps=ps)

    # resize the warps too by concatenating resize affine transformation to warp
    warpsetlist_out2 = []
    for warp in (warpsetlist_out):
        warp_out = delayed(resize_warp)(ps, warp, nl_mean_brain, suffix="_rsz")
        warpsetlist_out2.append(warp_out['dset_1'])

    # unifize the template
    if(ps.do_unifize_template):
        nl_mean_brain = delayed(unifize)(ps, dset=nl_mean_brain, suffix="_un")

    # anisotropically smooth the template too
    if(ps.aniso_iters):
        iters = ps.aniso_iters

    nl_mean_brain = delayed(aniso_smooth)(
        ps, dset=nl_mean_brain, suffix="_as", iters=iters)

    # return resized (and possibly unifized and anisotropically smoothed) mean
    #  brain and resized warps
    return {'nl_mean_brain': nl_mean_brain, 'aa_brains_out': aa_brains_out,
            'warpsetlist_out': warpsetlist_out2}


def get_upsample_val(upsample_level):
    """
    make dictionary to upsample at only one level
    """
    upsample_dict = {}
    for ii in range(5):
        if ii == upsample_level:
            upsample_dict[ii] = True
        else:
            upsample_dict[ii] = False
    return upsample_dict


def get_nl_mean(ps, delayed, basedset, aa_brains, warpsetlist, resize_brain):
    """
    do 5 levels of nonlinear warping
    at each level, warp a smaller neighborhood of voxels
    following pattern of @toMNI_Qwarpar
    """

    nl_mean_brain = basedset
    upsample_dict = get_upsample_val(ps.upsample_level)
    kwargs_dict = {
        0: {'qw_opts': '-blur 0 9 -minpatch 101 -lite', 'inilev': 0,
            'suffix': '_nl0', 'upsample': upsample_dict[0], 'nl_level': 0},
        1: {'qw_opts': '-blur 1 6 -minpatch 49 -lite', 'inilev': 2,
            'suffix': '_nl1', 'iniwarplevel': '0',
            'upsample': upsample_dict[1], 'nl_level': 1},
        2: {'qw_opts': '-blur 0 4 -minpatch 23 -lite', 'inilev': 5,
            'suffix': '_nl2', 'iniwarplevel': '1',
            'upsample': upsample_dict[2], 'nl_level': 2},
        3: {'qw_opts': '-blur 0 -2 -minpatch 13 -lite', 'inilev': 7,
            'suffix': '_nl3', 'iniwarplevel': '2',
            'upsample': upsample_dict[3], 'nl_level': 3},
        4: {'qw_opts': '-blur 0 -2 -minpatch 9  -lite', 'inilev': 9,
            'suffix': '_nl4', 'iniwarplevel': '3',
            'upsample': upsample_dict[4], 'nl_level': 4}
    }

    if ps.nl_level_only == -1:
        levels = range(5)
    else:
        levels = range(ps.nl_level_only, 5)
    for level in levels:
        # upsampling only happens at one level - here if upsampling
        if(level == ps.upsample_level):
            us_output = upsample_subjects_bases(ps, delayed, nl_mean_brain,
                                                aa_brains, warpsetlist, resize_brain, **kwargs_dict[level])
            nl_mean_brain = us_output['mean_brain_us']
            resize_brain = us_output['resize_brain_us']
            aa_brains = us_output['aa_brains_us']
            warpsetlist = us_output['warpsetlist_us']
        # may want to find a "typical" brain as intermediate restart
        # this subject has least deformation to current mean brain
        if(level == ps.findtypical_level):
            print("finding typical!")
            typical_brain = find_typical_subject(
                ps, delayed, aa_brains, warpsetlist)
            nl_mean_brain = typical_brain
        # do the nonlinear level of warping toward the current mean
        # with the latest parameters for that level
        nl_output = get_nl_leveln(
            ps,
            delayed,
            nl_mean_brain,
            aa_brains,
            warpsetlist,
            resize_brain,
            **kwargs_dict[level])

        # new mean brain across subjects- target for next level
        nl_mean_brain = nl_output['nl_mean_brain']
        # warps from this level are used for subsequent levels
        warpsetlist = nl_output['warpsetlist_out']
        # use output brains only for final output
        aa_brains_out = nl_output['aa_brains_out']

    # return the mean brain template and the warps
    return (nl_mean_brain, warpsetlist, aa_brains_out)


def warp_fs_seg(ps, fs_seg, aa_brain, warp, suffix="_warped"):
    raise ValueError(
        "Need to fix this because path now can't be passed through")
    fs_seg_out = prepare_afni_output(fs_seg, suffix)
    """
    warp FreeSurfer segmentation to template space
    using affine warp and nonlinear warp
    account for center shift if needed
    provide affine brain (aa_brain) for affine matrix
    and grid (should be same grid and space as final template brain)
    warp is nonlinear warp from 3dQwarp from affine to target
    """
    # change directory to aa_brain output, even with input segmentation
    # in another directory

    # may need align centers shift.1D file too
    # shift_mat = "*_ac_shft.1D"
    # copy FreeSurfer segmentation to current directory,
    # recenter first with @Align_Centers instead of adding to warps
    # because warp including shifts is expensive in memory and performance
    # replace segmentation with recentered version
    # this method costs a little disk space for the extra copy of FreeSurfer
    # segmentation
    fs_seg = align_centers(ps, dset=fs_seg, basedset=aa_brain,
                           suffix="_ac")

    # affine matrix named similarly as affine dataset
    aff_matrix = "%s.Xaff12.1D" % aa_brain.out_prefix()

    input_name = fs_seg.ppv()
    out_prefix = fs_seg_out.out_prefix()
    if ps.rewrite:
        rewrite = " -overwrite "
    else:
        rewrite = ""
    master = aa_brain.prefix()
    warp_name = warp.prefix()
    cmd_str = """\
        3dNwarpApply -NN -prefix {out_prefix} -master {master} -input {input_name} -nwarp \'{warp_name} {aff_matrix}\' \
            {rewrite}
    """
    cmd_str = cmd_str.format(**locals())
    # check if output dataset was created
    fs_seg_out = run_check_afni_cmd(cmd_str, ps, {'dset_1': fs_seg_out},
                                    "Could not transform FreeSurfer segmentation using")

    return (fs_seg_out)


def transform_freesurf_segs(ps, delayed, fs_segs, aa_brains, warpsetlist):
    # warp all the freesurfer segmentations to the final template space
    fs_segs_out = []
    for (fs_seg, aa_brain, warp) in zip(fs_segs, aa_brains, warpsetlist):
        # warp FreeSurfer segmentation to template space
        fs_seg_out = delayed(warp_fs_seg)(
            ps, fs_seg, aa_brain, warp, suffix="_FS_final")

        # add the outputs to the list
        fs_segs_out.append(fs_seg_out)

    # return final space version of freesurfer segmentation
    return {'fs_segs_out': fs_segs_out}


def compute_probmaps(ps, delayed, fs_segs):
    """
    compute probability of each region
    for every region, find how often it occurs at each voxel
    maybe start in new temporary directory to keep all
    the region prob. maps.
    maybe combine probmaps into one dataset, but then 3dMean
    wouldn't be used to compute max, argmax.
    get roilist from header of fs_segs dataset
    must use renum dataset generated by @SUMA_Make_spec_FS
    to get consistent numbering across subjects

   """
    fs_probmaps = []
   # for roi in roilist:
    # compute mean by region index
    # 3dMean fs_segs'[roi]'
    # with Dask, this will be parallelized across regions
    #  instead of subjects, as in most other places in this code
    # this should be like compute_mean just limited to index value
    # fs_probmap = delayed(compute_mean_index(ps,roi,fs_segs, suffix="_pm")
    # fs_probmaps.append(fs_probmap)

    return fs_probmaps


def compute_mpm(ps, delayed, fs_probmaps):
    """
    compute maximum probability map (MPM) across all probability maps
    i.e. the region index that occurs the most often at each voxel
    compute max probability and the index of the maximum probability
     while not considering probabilities below threshold
     **** need to modify 3dMean to compute argmax+1 (or argmax) with min threshold
    modally smooth resulting map
    return index of maximum at each voxel map (the maximum probability map)
    """
    fs_segs_out = []
    return {'fs_segs_out': fs_segs_out}


def make_freesurf_mpm(ps,
                      delayed, fs_segs, aligned_brains, nl_warpsetlist,
                      suffix="_FS_MPM"):
    """
    transform maximum probability map (MPM) atlas from
    FreeSurfer segmentation
    """
    fs_segs_out = transform_freesurf_segs(ps,
                                          delayed, fs_segs, aligned_brains, nl_warpsetlist)
    mpm = compute_mpm(ps, delayed, fs_segs_out)


def get_indata(dsetlist, outdir, delayed):
    # Get list of datasets and check we have no duplicate filenames
    dsetlist = [Path(p).absolute() for p in dsetlist]
    if len(dsetlist) != len({p.name for p in dsetlist}):
        raise ValueError("Some filenames (this does not exclude the directory"
                         " in the file path) are not unique. This cannot occur.")

    # Change current work directory to the output directory
    outdir = Path(outdir).absolute()
    if not outdir.exists():
        outdir.mkdir()
    os.chdir(outdir)

    # Copy the input dset paths into the output directory and make dataset
    # objects for use in the pipeline
    dsets = []
    indir = Path("input_data")
    if not indir.exists():
        indir.mkdir()
    for d in dsetlist:
        dpath = indir / d.name
        shutil.copy(str(d), dpath)

        dsets.append(ab.afni_name(dpath, strict=True))
    return dsets

    # dsetlist = [os.path.relpath(p,outdir) for p in dsetlist]


def get_task_graph(ps, delayed):
    """
    main computations here - create graph of processes
    """
    dsetlist = ps.dsets.parlist
    dsets = get_indata(dsetlist, ps.odir, delayed)

    warpsetlist = []
    (rigid_mean_brain, aligned_brains) = get_rigid_mean(
        ps, ps.basedset, dsets, delayed)
    (affine_mean_brain, aligned_brains) = get_affine_mean(
        ps, rigid_mean_brain, aligned_brains, delayed)

    if ps.resizebase:
        resize_brain = ps.resizebase
    else:
        resize_brain = affine_mean_brain

    (nl_mean_brain, nl_warpsetlist, nl_aligned_brains) = get_nl_mean(ps,
                                                                     delayed,
                                                                     affine_mean_brain,
                                                                     aligned_brains,
                                                                     warpsetlist,
                                                                     resize_brain
                                                                     )

    # transform maximum probability map (MPM) atlas from
    # FreeSurfer segmentation
    if ps.do_freesurf_mpm:
        raise ValueError(
            'Using do_freesurf_mpm is not yet implemented because fs_segs has not been defined.')
        # this also needs to generate a task_graph_dict
        freesurf_mpm = make_freesurf_mpm(ps,
                                         delayed, fs_segs, aligned_brains, nl_warpsetlist,
                                         suffix="_FS_MPM")

    else:
        task_graph_dict = OrderedDict([
            ('nl_mean_brain', nl_mean_brain),
            ('nl_warpsetlist', nl_warpsetlist),
            ('nl_aligned_brains', nl_aligned_brains)
        ])

    # nl_mean_brain template and MPM atlas are our final output
    # This is non-blocking. We can continue
    # our python session. Whenever we query the affine object
    # we will be informed of its status.

    print("Configured first processing loop")
    return task_graph_dict