#!/usr/bin/env python
# -*- coding: utf-8 -*-

import afni_python.afni_base as ab
from glob import glob
import os
import time


def align_centers(ps, dset=None, base=None, suffix="_ac", new_dir=1):
    # align the center of a dataset to the center of another
    # dataset like a template
    print("align centers of %s to %s" %
          (dset.out_prefix(), base.out_prefix()))

    if(dset.type == 'NIFTI'):
        # copy original to a temporary file
        print("dataset input name is %s" % dset.input())
        ao = ab.strip_extension(dset.input(), ['.nii', 'nii.gz'])
        print("new AFNI name is %s" % ao[0])
        aao = ab.afni_name("%s" % (ao[0]))
        aao.to_afni(new_view="+orig")
        o = ab.afni_name("%s%s%s" % (aao.out_prefix(), suffix, aao.view))
        ndir = ab.afni_name("%s%s" % (aao.out_prefix(), aao.view))
    else:
        o = dset.new("%s%s" % (dset.out_prefix(), suffix))
        ndir = ab.afni_name("%s%s" % (aao.out_prefix(), aao.view))

    if(new_dir == 1):
        # end with a slash
        output_dir = "%s/" % os.path.realpath("%s/%s" %
                                              (ps.odir, ndir.out_prefix()))
        print("# User has selected a new output directory %s" % output_dir)
        com = ab.shell_com(("mkdir %s" % output_dir),
                           ps.oexec, trim_length=2000)
        com.run()
        # give the OS and filesystems a couple seconds
        time.sleep(2)
        print("cd %s" % output_dir)
        if(not ps.dry_run()):
            os.chdir(output_dir)
        o.path = output_dir

    # use shift transformation of centers between grids as initial
    # transformation. @Align_Centers (3drefit)
    copy_cmd = "3dcopy %s %s" % (dset.ppv(), o.ppv())
    # may not actual need to do the centering, but still copy to new directory
    if(ps.do_center == 0):
        cmd_str = copy_cmd
    else:
        cmd_str = "%s; @Align_Centers -base %s -dset %s -no_cp" %     \
            (copy_cmd, base.input(), o.input())
    print("executing:\n %s" % cmd_str)
    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            print("** ERROR: Could not align centers using \n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())

    return o


def automask(ps, dset=None, suffix="_am"):
    # automask - make simple mask
    print("automask %s" % dset.out_prefix())

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
    o.path = dset.path
    cmd_str = "3dAutomask -dilate 3 -apply_prefix %s %s" %     \
        (o.out_prefix(), dset.input())
    print("executing:\n %s" % cmd_str)
    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            print("** ERROR: Could not automask using \n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())

    return o


def skullstrip(ps, dset=None, suffix="_ns"):
    # skullstrip
    print("skullstrip %s" % dset.out_prefix())
    if(ps.do_skullstrip == 0):
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
    o.path = dset.path
    cmd_str = "3dSkullStrip -prefix %s -input %s -push_to_edge" %     \
        (o.out_prefix(), dset.input())
    print("executing:\n %s" % cmd_str)
    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            print("** ERROR: Could not skullstrip using \n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())

    return o


def unifize(ps, dset=None, suffix="_un"):
    # unifize - bias-correct a dataset
    print("unifize %s" % dset.out_prefix())
    if(ps.do_unifize == 0):
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
    cmd_str = "3dUnifize -gm -prefix %s -input %s" %     \
        (o.out_prefix(), dset.input())
    print("executing:\n %s" % cmd_str)
    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            print("** ERROR: Could not unifize using \n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())

    return o


def rigid_align(ps, dset, base, suffix="_4rigid"):
    if(ps.do_rigid == 0):
        return dset
    os.chdir(dset.path)
    assert(dset is not None)
    o = dset.new("%s%s" % (dset.out_prefix(), suffix))
    o.path = dset.path
    if base.view == '':
        o.view = '+tlrc'
    else:
        o.view = base.view
    input_name = dset.pv()
    out_prefix = o.out_prefix()
    mat_exists = os.path.exists("%s_mat.aff12.1D" % out_prefix)
    base_in = base.input()
    # remove temp
    outaff_prefix = "%s_temp%s" % (dset.out_prefix(), suffix)
    outaff_name = "%s.HEAD %s.BRIK*" % (o.ppv(), o.ppv())
    if ps.rewrite:
        rewrite = " -overwrite "
    else:
        rewrite = ""
    # compute registration alignment to the base template
    # but apply only the rigid component and put into
    # grid of base template
    cmd_str = """\
    @auto_tlrc -base {base_in} -input {input_name} -no_ss \
    -rigid_equiv -suffix {suffix} -pad_input 15 -OK_maxite -maxite 50 \
    {rewrite} && \
    rm {outaff_name}; \
    3dAllineate -1Dmatrix_apply {out_prefix}.Xat.rigid.1D \
    -master {base_in} -prefix {out_prefix}  \
    -input {input_name} {rewrite}
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
    print(cmd_str)
    print('this is running')
    print("executing:\n %s" % cmd_str)
    # import pdb;pdb.set_trace()
    if (o.exist() and ps.ok_to_exist):
        print("Output already exists. That's okay")
        return o
    elif (not (o.exist() and mat_exists) or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        # ab.shell_com("echo Object in rigid align: %s"% repr(o), ps.oexec,trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            assert(False)
            print("** ERROR: Could not align rigidly using \n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())
    return o


def affine_align(ps, dset, base, suffix="_aff", aff_type="affine"):
    try:
        os.chdir(dset.path)
    except:
        os.chdir(os.path.abspath(os.path.dirname(dset)))
    assert(dset is not None)
    o = dset.new("%s%s" % (dset.out_prefix(), suffix))
    o.path = dset.path
    if base.view == '':
        o.view = '+tlrc'
    input_name = dset.pv()
    out_prefix = o.out_prefix()
    mat_exists = os.path.exists("%s_mat.aff12.1D" % out_prefix)
    base_in = base.input()
    # won't use affine output if rigid only is requested
    outaff_prefix = "%s_temp%s" % (dset.out_prefix(), suffix)
    outaff_name = "%s.HEAD %s.BRIK*" % (o.ppv(), o.ppv())
    if ps.rewrite:
        rewrite = " -overwrite "
    else:
        rewrite = ""
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
    {rewrite}
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
    print(cmd_str)
    print('this is running')
    print("executing:\n %s" % cmd_str)
    # import pdb;pdb.set_trace()

    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
        return o
    elif not (o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            assert(False)
            print("** ERROR: Could not align using \n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())
    # may only want just rigid, so just apply warp and delete the affine output
    if aff_type == 'rigid':
        cmd_str = """\
           rm {outaff_name}; \
           3dAllineate -1Dmatrix_apply {out_prefix}.Xat.rigid.1D \
           -master {base_in} -prefix {out_prefix}  \
           -input {input_name} {rewrite}
           """
        if (not (o.exist() and mat_exists) or ps.rewrite or ps.dry_run()):
            o.delete(ps.oexec)
            com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
            com.run(chdir="%s" % o.path)
            if (not o.exist() and not ps.dry_run()):
                assert(False)
                print("** ERROR: Could not align rigidly using \n  %s\n" % cmd_str)
                return None

    ab.shell_com("echo Object in rigid align: %s" %
                 repr(o), ps.oexec, trim_length=2000)
    return o


def aniso_smooth(ps, dset=None, suffix="_as", iters="3"):
    # anisotropically smooth data
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
    cmd_str = "3danisosmooth -matchorig  -3D -iters %s -prefix %s -mask %s %s" %     \
        (iters, o.out_prefix(), dset.input(), dset.input())
    print("executing:\n %s" % cmd_str)
    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            print("** ERROR: Could not anisotropically smooth using \n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())

    return o

# upsample a dataset to double its resolution - 8x number of voxels in 3D


def upsample_dset(ps, dset=None, suffix="_rs"):
    # resample data 2x (1/2 the voxel size)
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
    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            print("** ERROR: Could not upsample using:\n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())

    return o

# resample a dataset to grid of another dataset


def resample_dset(ps, dset, base, suffix="_rs"):
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
    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            print("** ERROR: Could not upsample using:\n  %s\n" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())

    return o


# find smallest dimension of dataset in x,y,z
def min_dim_dset(ps, dset=None):
    com = ab.shell_com(
        "3dAttribute DELTA %s" % dset.input(), ps.oexec, capture=1)
    if ps.dry_run():
        return (1.234567)
    else:
        com.run()

    min_dx = min([abs(float(com.val(0, i))) for i in range(3)])

    if(min_dx == 0.0):
        min_dx = 1.0
    return (min_dx)


def get_mean_brain(ps, dset_list, dset_glob, suffix="_rigid"):
    assert(dset_list[0] is not None)
    # end with a slash
    print("cd %s" % ps.odir)
    if(not ps.dry_run()):
        os.chdir(ps.odir)

    o = dset_list[0].new("mean%s" % (suffix))
    o.path = ps.odir

    cmd_str = """\
    3dMean -prefix mean{suffix}  {dset_glob}; \
    3dMean -stdev -prefix stdev{suffix} {dset_glob}
    """
    cmd_str = cmd_str.format(**locals())
    print("executing:\n %s" % cmd_str)

    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not o.exist() or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        com.run(chdir="%s" % o.path)
        if (not o.exist() and not ps.dry_run()):
            assert(False)
            print("** ERROR: Could not compute mean using %s" % cmd_str)
            return None
    else:
        ps.exists_msg(o.input())

    return o

# change directory here
# separate function just for dask delay


def change_dirs(dset_list, ps, path="."):
    print("cd %s" % path)
    if(not ps.dry_run()):
        os.chdir(self.path)

    # just return this for dask
    return dset_list

# first iteration - compute rigid mean across all subjects


def get_rigid_mean(ps, basedset, dsetlist, delayed):

    aligned_brains = []

    cwd = os.path.abspath(os.curdir)
    if cwd != '/':
        cwd += '/'

    # from dask import delayedsetup using dask delayed
    for dset_name in dsetlist:

        start_dset = ab.afni_name(dset_name)

        # start off just aligning the centers of the datasets
        aname = delayed(align_centers)(ps, dset=start_dset, base=basedset)
        amname = delayed(skullstrip)(ps, dset=aname)
        dname = delayed(unifize)(ps, dset=amname)
        af_aligned = delayed(rigid_align)(ps, dset=dname,
                                          base=basedset, suffix="_4rigid")

        # change back to original directory
        # af_aligned_cd = delayed(change_dirs)(af_aligned,ps, path=cwd)

        #  We can continue our python session. Whenever we query the affine
        # object we will be informed of its status.
        aligned_brains.append(af_aligned)

    # print(aligned_brains)
    rigid_mean_brain = delayed(get_mean_brain)(
        aligned_brains,
        ps,
        dset_glob="*/*_4rigid+tlrc.HEAD",
        suffix="_rigid")

    print("Configured first processing loop")
    align_obj = (rigid_mean_brain, aligned_brains)

    # return the rigid mean brain template and the rigidly aligned_brains
    # return rigid_mean_brain, aligned_brains
    return (rigid_mean_brain, aligned_brains)

# 2nd iteration - compute affine mean across all subjects


def get_affine_mean(ps, basedset, dsetlist, delayed):

    aligned_brains = []

    cwd = os.path.abspath(os.curdir)
    if cwd != '/':
        cwd += '/'

    # this time, we don't need to do all the other steps again
    #  if we're using the stripped, unifized
    for dset in dsetlist:
        af_aligned = delayed(affine_align)(
            ps, dset, base=basedset, suffix="_affx")

        # change back to original directory
        # af_aligned_cd = delayed(change_dirs)(af_aligned,ps, path=cwd)

        #  We can continue our python session. Whenever we query the affine
        # object we will be informed of its status.
        aligned_brains.append(af_aligned)

    print(aligned_brains)
    affine_mean_brain = delayed(get_mean_brain)(
        aligned_brains,
        ps,
        dset_glob="*/*_affx+tlrc.HEAD",
        suffix="_affx")

    print("Configured first processing loop")
    # return the rigid mean brain template and the rigidly aligned_brains
    # Dask can't return two separate objects, so combine into a single tuple
    return (affine_mean_brain, aligned_brains)

# prepare the output for an afni function
#  make AFNI dataset structure based on input name, additional suffix and master dataset
# could have list of outputs with list of suffixes


def prepare_afni_output(ps, dset, suffix, master=[]):
    try:
        os.chdir(dset.path)
    except:
        os.chdir(os.path.abspath(os.path.dirname(dset)))
    assert(dset is not None)
    o = dset.new("%s%s" % (dset.out_prefix(), suffix))
    o.path = dset.path
    if master:
        if master.view == '':
            o.view = '+tlrc'
    return o

# run afni command and check if afni output dataset exists
# return the same output dataset if it exists, otherwise return None
# could have list of outputs


def run_check_afni_cmd(cmd_str, ps, o, message):

    print("command:\n %s" % cmd_str)
    # import pdb;pdb.set_trace()
    if ps.ok_to_exist and o.exist():
        print("Output already exists. That's okay")
    elif (not (o.exist()) or ps.rewrite or ps.dry_run()):
        o.delete(ps.oexec)
        com = ab.shell_com(cmd_str, ps.oexec, trim_length=2000)
        print("Running in %s" % o.path)
        com.run(chdir="%s" % o.path, capture=1)
        if (not o.exist() and not ps.dry_run()):
            # print error message from com
            raise ValueError("** ERROR: %s \n  %s\n" % (message, cmd_str))
    else:
        ps.exists_msg(o.input())
    return o

# nonlinearly align dataset to a base dataset
# initial warp provided by either iniwarpset as an AFNI dataset
# or by iniwarplevel and composed by name dset_nlx_WARP+tlrc
# with x as a digit string here (0,1,2,3)
# returns warped dataset and WARP dataset of deformation distances


def nl_align(ps, dset, base, warp, **kwargs):
    # create output dataset structure
    o = prepare_afni_output(ps, dset, suffix, base)

    # make warp dataset structure too
############
# NOPE THIS SHOULD JUST BE WARPED_BRAINS, and this function can do the iteration.
    warpset = dset.new("%s%s_WARP" % (dset.out_prefix(), suffix))
##############
    input_name = dset.pv()
    out_prefix = o.out_prefix()
    base_in = base.input()
    # if warp dataset provided here, use it
    if iniwarpset:
        iniwarp = "-iniwarp %s" % iniwarpset.input()
    else:
        # if just a level is provided for the initial warp, compose the name here
        if(iniwarplevel):
            # # upsample the warp dataset in the same way as 3dQwarp upsamples data to base"
            # if upsample:
            #     iniwarpset = dset.new("%s_nl%s_WARP" %
            #                           (dset.out_prefix(), iniwarplevel))
            #     resample_dset(ps, iniwarpset, base, suffix="_us")
            #     iniwarp = "-iniwarp %s_nl%s_WARP_us+tlrc" % (
            #         dset.out_prefix(), iniwarplevel)
            # # provide name of warp dataset
            # else:
                iniwarp = "-iniwarp %s_nl%s_WARP+tlrc" % (
                    dset.out_prefix(), iniwarplevel)
        # otherwise, no initial warp given, so skip the initial warp for 3dQwarp
        else:
            iniwarp = ""
    if ps.rewrite:
        rewrite = " -overwrite "
    else:
        rewrite = ""
    # may need to resample to higher resolution base
    if upsample:
        upsample_opt = "-resample"
    else:
        upsample_opt = ""
    cmd_str = """\
    3dQwarp -base {base_in} -source {input_name} \
    -prefix {out_prefix} {qw_opts} \
    {iniwarp} {rewrite} {upsample_opt}
    """

    cmd_str = cmd_str.format(**locals())

    # check if output dataset was created
    o = run_check_afni_cmd(cmd_str, ps, o, "Could not nonlinearly align using")

    return {'aa_brain' : aa_brain,'warp': warp}


def get_nl_leveln(ps, delayed, target_brain, aa_brains, warpsetlist,resize_brain, **kwargs):

    # if upsample:
    #     target_brain = delayed(upsample_dset)(ps, dset=target_brain, suffix="_rs")
    #     resize_brain = delayed(upsample_dset)(
    #         ps, dset=resizebase, suffix="_rs")
    #     warpsetlist = delayed(get_upsample_dset_list)(warpsetlist)
    # need get_upsample_dset_list function


    if not warpsetlist:
        warpsetlist = [''] * len(aa_brains)

    aa_brains_out = []
    warpsetlist_out = []
    # af_aligned, nlwarp_out
    for (aa_brain, warp) in zip(aa_brains,warpsetlist):
        brain_and_warp  = delayed(nl_align)(
        ps, aa_brain, target_brain, warp, **kwargs)
        aa_brains_out.append(brain_and_warp['aa_brain'])
        warpsetlist_out.append(brain_and_warp['warp'])

    nl_mean_brain = delayed(get_mean_brain)(
        ps,
        aa_brains_out,
        dset_glob=("*/*%s+tlrc.HEAD" % kwargs['suffix']),
        suffix=kwargs['suffix'])



    # adjust size to avoid dilation and to match group
    # trying this out, Bob's 3dNwarpAdjust mostly works too. Could do affine at just last step.
    # may want more specialized function here instead - no shears,...
    nl_mean_brain = delayed(affine_align)(ps, nl_mean_brain, resize_brain,
                                          suffix="_rsz", aff_type="affine")
    # nl_mean_brain = resize_template(nl_mean_brain, ps.resizebase)

    # unifize the template
    nl_mean_brain = delayed(unifize)(ps, nl_mean_brain, suffix="_un")

    # anisotropically smooth the template too
    if(ps.aniso_iters):
        iters = ps.aniso_iters

    nl_mean_brain = delayed(aniso_smooth)(
        ps, nl_mean_brain, suffix="_as", iters=iters)


    return {'nl_mean_brain': nl_mean_brain, 'aa_brains_out' : aa_brains_out, 'warpsetlist_out': aa_brains_out}

# 3rd iteration - set of nonlinear iterations - compute nonlinear mean across all subjects

def get_upsample_val(upsample_level):
    upsample_dict = {}
    for ii in range(5):
        if ii == upsample_level:
            upsample_dict[ii] = True
        else:
            upsample_dict[ii] = False
    return upsample_dict

def get_nl_mean(ps, delayed, basedset, aa_brains, warpsetlist, resize_brain):
    # do 5 levels of nonlinear warping
    # at each level, warp a smaller neighborhood of voxels
    # following pattern of @toMNI_Qwarpar
    nl_mean_brain = basedset
    upsample_dict = get_upsample_val(ps.upsample_level)
    kwargs_dict = {
        0: {'qw_opts': '-blur 0 9 -minpatch 101',
            'suffix': '_nl0', 'upsample': upsample_dict[0]},
        1: {'qw_opts': '-blur 1 6 -inilev 2  -minpatch 49',
            'suffix': '_nl1', 'iniwarplevel': '0', 'upsample': upsample_dict[1]},
        2: {'qw_opts': '-blur 0 4 -inilev 5  -minpatch 23',
            'suffix': '_nl2', 'iniwarplevel': '1', 'upsample': upsample_dict[2]},
        3: {'qw_opts': '-blur 0 -2 -inilev 7  -minpatch 13',
            'suffix': '_nl3', 'iniwarplevel': '2', 'upsample': upsample_dict[3]},
        4: {'qw_opts': '-blur 0 -2 -inilev 9  -minpatch 9',
            'suffix': '_nl4', 'iniwarplevel': '3', 'upsample': upsample_dict[4]}
    }

    if ps.nl_level_only == -1:
        levels = range(5)
    else:
        levels = range(ps.nl_level_only,5)
    for level in levels:
        nl_output = get_nl_leveln(
            ps,
            delayed,
            nl_mean_brain,
            aa_brains,
            warpsetlist,
            resize_brain,
            **kwargs_dict[level])
        nl_mean_brain = nl_output['nl_mean_brain']
        aa_brains = nl_output['aa_brains_out']
        warpsetlist = nl_output['warpsetlist_out']

    # return the mean brain template and the warps
    return (nl_mean_brain, warpsetlist,aa_brains)


# def set_new_base(ps, dset, taskgraph, delayed):
    # instead of doing this lets just pass in the base image as an argument
    # ps.basedset = dset
    # return(taskgraph)

# main computations here - create graph of processes


def get_task_graph(ps, delayed):
    # if ps.do_rigid_only:
    #     (rigid_mean_brain, aligned_brains) = get_rigid_mean(ps,basedset, dsetlist, delayed)
    #     return task_graph
    # if ps.do_affine_only:
    #     dsetlist = []
    #     # convert names of datasets into dataset list structure
    #     for dset_name in ps.dsets.parlist:
    #         start_dset = ab.afni_name(dset_name)
    #         dsetlist.append(start_dset)
    #     task_graph = get_affine_mean(ps,ps.basedset, dsetlist, delayed)
    #     return task_graph
    # if ps.do_nl_only:
    #     if(ps.resizebase is not None):
    #         ps.resizebase = ps.basedset
    #     dsetlist = []
    #     # convert names of datasets into dataset list structure
    #     for dset_name in ps.dsets.parlist:
    #         start_dset = ab.afni_name(dset_name)
    #         dsetlist.append(start_dset)
    #     warpsetlist = []
    #     # convert names of warp datasets into dataset list structure
    #     if(ps.warpsets and ps.warpsets.parlist):
    #         for dset_name in ps.warpsets.parlist:
    #             start_dset = ab.afni_name(dset_name)
    #             warpsetlist.append(start_dset)

    #     task_graph = get_nl_mean(ps, dsetlist, warpsetlist, delayed)
    #     return task_graph
    dsetlist = ps.dsets.parlist
    if ps.warpsets:
        warpsetlist = ps.warpsets.parlist
    else:
        warpsetlist = []

    (rigid_mean_brain, aligned_brains) = get_rigid_mean(
        ps, ps.basedset, dsetlist, delayed)
    # task_graph = set_new_base(ps, rigid_mean_brain, aligned_brains, delayed)
    (affine_mean_brain, aligned_brains) = get_affine_mean(
        ps, rigid_mean_brain, aligned_brains, delayed)

    if ps.resizebase:
        resize_brain = ps.resizebase
    else:
        resize_brain = affine_mean_brain

    task_graph = get_nl_mean(ps,
                             delayed,
                             affine_mean_brain,
                             aligned_brains,
                             warpsetlist,
                             resize_brain
                             )
#    affine_mean_brain = delayed(get_affine_mean)(ps, aligned_brains)
#    ps.basedset = affine_mean_brain
#    ps.resizebase = affine_mean_brain
#    nl_mean_brain = delayed(get_nl_mean)(ps, aligned_brains)

    # nl_mean_brain is our final output
    # This is non-blocking. We can continue
    # our python session. Whenever we query the affine object
    # we will be informed of its status.

    print("Configured first processing loop")
    return task_graph
