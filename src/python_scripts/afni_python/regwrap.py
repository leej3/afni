import sys
import os
from pprint import pformat
# sys.path.append('/data/NIMH_SSCC/template_making/scripts')

# AFNI modules
import afni_python.afni_base as ab
import afni_python.afni_util as au
from afni_python.option_list import OptionList, read_options
# from align_epi_anat import RegWrap

# class TemplateWrap(RegWrap):
#     def __init__(self, label):
#         super().__init__(self, label)

class RegWrap():
    def __init__(self, label):
        # software version (update for changes)
        self.make_template_version = "0.02"
        # user assigned path for output (not used yet)
        self.output_dir = 'iterative_template_dir'
        self.ok_to_exist = 0 #Fail if weight data exists
        self.label = label
        self.valid_opts = None
        self.user_opts = None
        self.verb = 1    # a little talkative by default
        self.save_script = ''  # save completed script into given file
        self.rewrite = 0  # Do not recreate existing volumes
        self.oexec = ""  # dry_run is an option
        self.rmrm = 1   # remove temporary files
        self.prep_only = 0  # do preprocessing only
        self.odir = os.getcwd()
        self.bokeh_port = 8787 # default port to show graphical Bokeh debugging info with Dasks
        self.daskmode = "None" # which kind of Dask parallelization, none by default
        self.resizebase = [] # dataset to resize nonlinear means to

        self.do_skullstrip = 1  # steps to do
        self.do_unifize = 1
        self.do_center = 1
        self.do_rigid = 1
        self.do_affine = 1
        self.do_nonlinear = 1
        self.do_anisosmooth = 0
        self.do_unifize_template = 0
	
        self.do_rigid_only = 0   # major stages to do when doing just one
        self.do_affine_only = 0
        self.do_nl_only = 0
        self.nl_level_only = -1  # do only one level of nonlinear alignment

        self.max_workers = 0   # user sets maximum number of workers
        self.max_threads = 0   # user sets maximum number of threads
        self.warpsets = []
        self.cluster_queue = []
        self.cluster_memory = []
        self.cluster_constraint = []
        self.cluster_walltime = []
        self.aniso_iters = "3"
        self.upsample_level = [] # no upsampling by default
        return

    def init_opts(self):
        self.valid_opts = OptionList('init_opts')

        # input datasets
        self.valid_opts.add_opt('-ok_to_exist', 0, [],
        helpstr="For running make_template_dask in parallel. This\n" 
               "flag allows a previous output of the weight dataset \n"
               "to be used.")
        self.valid_opts.add_opt('-dsets', -1, [],
                                helpstr="Names of datasets")
        self.valid_opts.add_opt('-init_base', 1, [],
                                helpstr="Name of initial base dataset")
        self.valid_opts.add_opt('-resize_base', 1, [],
                                helpstr="Name of resizing dataset")

        self.valid_opts.add_opt('-keep_rm_files', 0, [],
                                helpstr="Don't delete any of the temporary files created here")
        self.valid_opts.add_opt('-prep_only', 0, [],
                                helpstr="Do preprocessing steps only without alignment")
        self.valid_opts.add_opt('-help', 0, [],
                                helpstr="The main help describing this program with options")
        self.valid_opts.add_opt('-limited_help', 0, [],
                                helpstr="The main help without all available options")
        self.valid_opts.add_opt('-option_help', 0, [],
                                helpstr="Help for all available options")
        self.valid_opts.add_opt('-version', 0, [],
                                helpstr="Show version number and exit")
        self.valid_opts.add_opt('-ver', 0, [],
                                helpstr="Show version number and exit")
        self.valid_opts.add_opt('-verb', 1, [],
                                helpstr="Be verbose in messages and options")
        self.valid_opts.add_opt('-save_script', 1, [],
                                helpstr="save executed script in given file")

        self.valid_opts.add_opt('-no_center', 0, [],
                                helpstr="Do not align centers of datasets to initial base")
        self.valid_opts.add_opt('-no_strip', 0, [],
                                helpstr="Do not remove skull")
        self.valid_opts.add_opt('-no_unifize', 0, [],
                                helpstr="Do not unifize data intensities across subjects")
        self.valid_opts.add_opt('-no_anisosmooth', 0, [],
                                helpstr="Do not anisotropically smooth the mean templates")

        self.valid_opts.add_opt('-no_rigid', 0, [],
                                helpstr="Do not do rigid alignment step,\n"
                                        "use base as input to affine stage")
        self.valid_opts.add_opt('-no_affine', 0, [],
                                helpstr="Do not do affine alignment step,\n"
                                        "use base as input to nonlinear stage")
        self.valid_opts.add_opt('-no_nonlinear', 0, [],
                                helpstr="Do not do nonlinear alignment step,\n"
                                        "use base as input to nonlinear stage")

        self.valid_opts.add_opt('-rigid_only', 0, [],
                                helpstr="Only do rigid alignment step")
        self.valid_opts.add_opt('-affine_only', 0, [],
                                helpstr="Only do affine alignment step")
        self.valid_opts.add_opt('-nl_only', 0, [],
                                helpstr="Only do nonlinear alignment step")
        self.valid_opts.add_opt('-nl_level_only', 1, [],
                                helpstr="Only do a single nonlinear level alignment step\n"
                                        "providing a level from 0 to 4 to do")
        self.valid_opts.add_opt('-upsample_level', 1, [],
                                helpstr="Upsample base and warp starting at a single\n"
                                        "nonlinear alignment level providing a level from 0 to 4")

        self.valid_opts.add_opt('-overwrite', 0, [],
                                helpstr="Overwrite existing files")
        self.valid_opts.add_opt('-dask_mode', 1, ['None'], ['None', 'SLURM', 'localcluster'],
                                helpstr="set Dask parallelization type")
        self.valid_opts.add_opt('-bokeh_port', 1, ['8787'],
                                helpstr="port for Bokeh visual debugging info with Dask")
        self.valid_opts.add_opt('-max_workers', 1, [],
                                helpstr="maximum number of cpus used for this Dask process")
        self.valid_opts.add_opt('-max_threads', 1, [],
                                helpstr="maximum number of threads used for this Dask process")
        self.valid_opts.add_opt('-cluster_queue', 1, [],
                                helpstr="SLURM queue partition (norm,nimh,...)")
        self.valid_opts.add_opt('-cluster_constraint', 1, [],
                                helpstr="SLURM node constraints (10g, iband,...)")
        self.valid_opts.add_opt('-cluster_walltime', 1, [],
                                helpstr="SLURM walltime limit (36:0:0,...)")
        self.valid_opts.add_opt('-cluster_memory', 1, [],
                                helpstr="SLURM cluster node memory minimum (20g)")
        self.valid_opts.add_opt('-warpsets', -1, [],
                                helpstr="Names of warp datasets if doing a specified nonlinear level")
        self.valid_opts.add_opt('-aniso_iters', 1, [],
                                helpstr="Number of iterations for anisotropical smoothing")


    def dry_run(self):
        if self.oexec != "dry_run":
            return 0
        else:
            return 1

    def apply_initial_opts(self, opt_list):
        opt1 = opt_list.find_opt('-version')  # user only wants version
        opt2 = opt_list.find_opt('-ver')
        if ((opt1 != None) or (opt2 != None)):
            # self.version()
            self.ciao(0)   # terminate
        opt = opt_list.find_opt('-verb')    # set and use verb
        if opt != None:
            self.verb = int(opt.parlist[0])

        opt = opt_list.find_opt('-save_script')  # save executed script
        if opt != None:
            self.save_script = opt.parlist[0]

        # user says it's okay to overwrite existing files
        opt = self.user_opts.find_opt('-overwrite')
        if opt != None:
            print("setting option to rewrite")
            self.rewrite = 1

        opt = opt_list.find_opt('-ex_mode')    # set execute mode
        if opt != None:
            self.oexec = opt.parlist[0]

        opt = opt_list.find_opt('-keep_rm_files')    # keep temp files
        if opt != None:
            self.rmrm = 0

        opt = opt_list.find_opt('-prep_only')    # preprocessing only
        if opt != None:
            self.prep_only = 1

        opt = opt_list.find_opt('-help')    # does the user want help?
        if opt != None:
            self.self_help(2)   # always give full help now by default
            self.ciao(0)  # terminate

        opt = opt_list.find_opt('-limited_help')  # less help?
        if opt != None:
            self.self_help()
            self.ciao(0)  # terminate

        opt = opt_list.find_opt('-option_help')  # help for options only
        if opt != None:
            self.self_help(1)
            self.ciao(0)  # terminate

        opt = opt_list.find_opt('-suffix')
        if opt != None:
            self.suffix = opt.parlist[0]
            if((opt == "") or (opt == " ")):
                self.error_msg("Cannot have blank suffix")
                self.ciao(1)

        opt = opt_list.find_opt('-bokeh_port')
        if opt != None:
            self.bokeh_port = int(opt.parlist[0])
            if((opt == "") or (opt == " ")):
                self.error_msg("Must provide a port number for bokeh port")
                self.ciao(1)

        opt = opt_list.find_opt('-max_workers')
        if opt != None:
            self.max_workers = int(opt.parlist[0])
            if((opt == "") or (opt == " ")):
                self.error_msg("Must provide an integer for number of Dask worker CPUs")
                self.ciao(1)

        opt = opt_list.find_opt('-max_threads')
        if opt != None:
            self.max_threads = int(opt.parlist[0])
            if((opt == "") or (opt == " ")):
                self.error_msg("Must provide an integer for number of Dask threads")
                self.ciao(1)

        opt = opt_list.find_opt('-dask_mode')
        if opt != None:
            self.daskmode = opt.parlist[0]
            if((opt == "") or (opt == " ")):
                self.error_msg("Must provide SLURM, localcluster or None for dask_mode")
                self.ciao(1)

        opt = opt_list.find_opt('-cluster_queue')
        if opt != None:
            self.cluster_queue = opt.parlist[0]
            if((opt == "") or (opt == " ")):
                self.error_msg("Must provide name of queue/partition to use in SLURM, e.g norm, nimh, quick, ...")
                self.ciao(1)

        opt = opt_list.find_opt('-cluster_constraint')
        if opt != None:
            self.cluster_constraint = opt.parlist[0]
            if((opt == "") or (opt == " ")):
                self.error_msg("Must specify which kinds of constraints for cluster nodes, e.g. 10g (default)")
                self.ciao(1)

        opt = opt_list.find_opt('-cluster_walltime')
        if opt != None:
            self.cluster_walltime = opt.parlist[0]
            if((opt == "") or (opt == " ")):
                self.error_msg("Must specify walltime limit for cluster nodes, e.g 36:0:0")
                self.ciao(1)

        opt = opt_list.find_opt('-cluster_memory')
        if opt != None:
            self.cluster_memory = opt.parlist[0]
            if((opt == "") or (opt == " ")):
                self.error_msg("Must specify minimum memory per cluster node, e.g 20g for 20 gigabytes or RAM/node")
                self.ciao(1)

        opt = opt_list.find_opt('-aniso_iters')
        if opt != None:
            self.aniso_iters = opt.parlist[0]
            try:
               tempiters = int(opt.parlist[0])
            except:
                self.error_msg("Must provide an integer for number of Dask worker CPUs")
                self.ciao(1)


    def get_user_opts(self,help_str):
        self.valid_opts.check_special_opts(sys.argv)  # ZSS March 2014
        self.user_opts = read_options(sys.argv, self.valid_opts)
        self.help_str = help_str
        if self.user_opts == None:
            return 1  # bad
        # no options: apply -help
        if (len(self.user_opts.olist) == 0 or len(sys.argv) <= 1):
            self.self_help()
            self.ciao(0)  # terminate
        if self.user_opts.trailers:
            opt = self.user_opts.find_opt('trailers')
            if not opt:
                print("** ERROR: seem to have trailers, but cannot find them!")
            else:
                print("** ERROR: have invalid trailing args: %s", opt.show())
            return 1  # failure

        # apply the user options
        if self.apply_initial_opts(self.user_opts):
            return 1

        if self.verb > 3:
            self.show('------ found options ------ ')

        return

    def show(self, mesg=""):
        print('%s: %s' % (mesg, self.label))
        if self.verb > 2:
            self.valid_opts.show('valid_opts: ')
        self.user_opts.show('user_opts: ')

    def info_msg(self, mesg=""):
        if(self.verb >= 1):
            print("#++ %s" % mesg)

    def error_msg(self, mesg=""):
        print("#**ERROR %s" % mesg)

    def exists_msg(self, dsetname=""):
        print("** Dataset: %s already exists" % dsetname)
        print("** Not overwriting.")
        if(not self.dry_run()):
            self.ciao(1)

    def ciao(self, i):
        if i > 0:
            print("** ERROR - script failed")
        elif i == 0:
            print("")

        os.chdir(self.odir)

        if self.save_script:
            au.write_afni_com_history(self.save_script)

        # return status code
        sys.exit(i)

        # save the script command arguments to the dataset history
    def save_history(self, dset, exec_mode):
        self.info_msg("Saving history")  # sounds dramatic, doesn't it?
        cmdline = au.args_as_command(sys.argv,
                                  '3dNotes -h "', '" %s' % dset.input())
        com = ab.shell_com("%s\n" % cmdline, exec_mode)
        com.run()

        # show help
        # if help_level is 1, then show options help only
        # if help_level is 2, then show main help and options help
    def self_help(self, help_level=0):
        if(help_level!=1) :
            print(self.help_str)
        if(help_level):
            print("A full list of options for %s:\n" % self.label)
            for opt in self.valid_opts.olist:
                print("   %-20s" % (opt.name))
                if (opt.helpstr != ''):
                    print("   %-20s   %s" %
                          ("   use:", opt.helpstr.replace("\n", "\n   %-20s   " % ' ')))
                if (opt.acceptlist):
                    print("   %-20s   %s" %
                          ("   allowed:", str.join(', ', opt.acceptlist)))
                if (opt.deflist):
                    print("   %-20s   %s" %
                          ("   default:", str.join(' ', opt.deflist)))
        return 1

    def version(self):
        self.info_msg("make_template_dask: %s" % self.make_template_version)

        # copy dataset 1 to dataset 2
        # show message and check if dset1 is the same as dset2
        # return non-zero error if can not copy
    def copy_dset(self, dset1, dset2, message, exec_mode):
        self.info_msg(message)
        if(dset1.input() == dset2.input()):
            print("# copy is not necessary")
            return 0
        #      if((os.path.islink(dset1.p())) or (os.path.islink(dset2.p()))):
        if(dset1.real_input() == dset2.real_input()):
            print("# copy is not necessary")
            return 0
        ds1 = dset1.real_input()
        ds2 = dset2.real_input()
        ds1s = ds1.replace('/./', '/')
        ds2s = ds2.replace('/./', '/')
        if(ds1s == ds2s):
            print("# copy is not necessary - both paths are same")
            return 0
        print("copying from dataset %s to %s" % (dset1.input(), dset2.input()))
        dset2.delete(exec_mode)
        com = ab.shell_com(
            "3dcopy %s %s" % (dset1.input(), dset2.out_prefix()), exec_mode)
        com.run()
        if ((not dset2.exist())and (exec_mode != 'dry_run')):
            print("** ERROR: Could not rename %s\n" % dset1.input())
            return 1
        return 0

        # BEGIN script specific functions
    def process_input(self):
        # Do the default test on all options entered.
        # NOTE that default options that take no parameters will not go
        # through test, but that is no big deal
        for opt in self.user_opts.olist:
            if (opt.test() == None):
                self.ciao(1)

        # user says it's okay if output dataset exists
        opt = self.user_opts.find_opt('-ok_to_exist')
        if opt != None:
            self.ok_to_exist = 1

        # center alignment is on by default
        opt = self.user_opts.find_opt('-no_center')
        if opt != None:
            self.center = 0

        # unifize is on by default
        opt = self.user_opts.find_opt('-no_unifize')
        if opt != None:
            self.do_unifize = 0

        # skull stripping is on by default
        opt = self.user_opts.find_opt('-no_strip')
        if opt != None:
            self.do_skullstrip = 0

        # anisotropically smooth is off by default now
        opt = self.user_opts.find_opt('-anisosmooth')
        if opt != None:
            self.do_anisosmooth = 1

        # unifize template off by default
        opt = self.user_opts.find_opt('-unifize_template')
        if opt != None:
            self.do_unifize_template = 1

        # rigid alignment is on by default
        opt = self.user_opts.find_opt('-no_rigid')
        if opt != None:
            self.do_rigid = 0

        # affine alignment is on by default
        # turning affine off implies rigid off too for now
        opt = self.user_opts.find_opt('-no_affine')
        if opt != None:
            self.do_rigid = 0
            self.do_affine = 0

        # nonlinear alignment is on by default
        # I'm going to take this to mean do the rigid and affine parts only
        opt = self.user_opts.find_opt('-no_nonlinear')
        if opt != None:
            self.do_nonlinear = 0

        # rigid alignment only
        opt = self.user_opts.find_opt('-rigid_only')
        if opt != None:
            self.do_rigid_only = 1

        # affine alignment only
        opt = self.user_opts.find_opt('-affine_only')
        if opt != None:
            self.do_affine_only = 1

        # nonlinear alignment only
        opt = self.user_opts.find_opt('-nl_only')
        if opt != None:
            self.do_nl_only = 1

        # nonlinear alignment only
        opt = self.user_opts.find_opt('-nl_level_only')
        if opt != None:
            self.do_nl_only = 1  # implied superset
            try:
                self.nl_level_only = int(opt.parlist[0])
            except:
                self.error_msg("Must provide a number from 0 to 4 for a specific nonlinear level")
                self.ciao(1)
            if((self.nl_level_only<0) or (self.nl_level_only>4)):
                self.error_msg("Must provide a number from 0 to 4 for a specific nonlinear level")
                self.ciao(1)

        # upsample base and then subsequent output starting at a specified nonlinear level
        opt = self.user_opts.find_opt('-upsample_level')
        if opt != None:
            try:
                self.upsample_level = int(opt.parlist[0])
            except:
                self.error_msg("Must provide a number from 0 to 4 for a specific nonlinear level")
                self.ciao(1)
            if((self.upsample_level<0) or (self.upsample_level>4)):
                self.error_msg("Must provide a number from 0 to 4 for a specific nonlinear level")
                self.ciao(1)

 
        opt = self.user_opts.find_opt('-dsets')
        if opt == None:
            print("** ERROR: Must use -dsets option to specify input datasets\n")
            self.ciao(1)
        self.dsets = self.user_opts.find_opt('-dsets')
        for dset_name in self.dsets.parlist:
            check_dset = ab.afni_name(dset_name)
            if not check_dset.exist():
                self.error_msg("Could not find dset\n %s "
                               % check_dset.input())
            else:
                self.info_msg(
                    "Found dset %s\n" % check_dset.input())

        opt = self.user_opts.find_opt('-warpsets')
 #       if((opt==None) and (self.nl_level_only>0)):
 #           self.error_msg("Must provide initial warp datasets if doing nonlinear levels> 0")
 #           self.ciao(1)
        if(opt):
            self.warpsets = self.user_opts.find_opt('-warpsets')
            for warpset_name in self.warpsets.parlist:
                check_dset = ab.afni_name(warpset_name)
                if not check_dset.exist():
                    self.error_msg("Could not find warp dset\n %s "
                                   % check_dset.input())
                else:
                    self.info_msg(
                        "Found warp dset %s\n" % check_dset.input())


        opt = self.user_opts.find_opt('-init_base')
        if opt == None:
             print(
                "** ERROR: Must use -init_base option to specify an initial base\n")
             self.ciao(1)

        self.basedset = ab.afni_name(opt.parlist[0])
        if not self.basedset.exist():
             self.error_msg("Could not find initial base dataset\n %s "
                           % self.basedset.input())
        else:
             self.info_msg(
                "Found initial base dset %s\n" % self.basedset.input())

        opt = self.user_opts.find_opt('-resize_base')
        if opt != None:
            self.resizebase = ab.afni_name(opt.parlist[0])
            if not self.resizebase.exist():
                 self.error_msg("Could not find resize base dataset\n %s "
                           % self.resizebase.input())
            else:
                 self.info_msg(
                     "Found resize base dset %s\n" % self.resizebase.input())

    def __repr__(self):
        return pformat(self.__dict__)

