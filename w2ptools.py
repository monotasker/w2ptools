#!/usr/bin/python

import sys
import re
import os
import glob
import pprint

"""
w3ptools: A suite of utility scripts designed to simplify working with the web2py web
development framework on a *nix based operating system.

At present w2ptools includes the following functions:

plugsync: Synchronize versions of a web2py plugin within a single web2py installation folder
"""
class sync(object):
    """Synchronize plugins within a single web2py directory"""

    def __init__(self):
        pass

    def syncit(self):
        fs_data = self.fs_data()

        pprint.pprint(fs_data)

        #create missing dirs
        base = os.path.abspath('.')
        for p, v in fs_data.items():
            for dir in v['dirs']:
                cdir = os.path.join(base, p, dir)
                if os.path.isdir(cdir):
                    print 'path ', cdir, 'already exists'
                else:
                    os.makedirs(cdir)
                    print 'created ', cdir

    def fs_data(self):
        """
        Return a dictionary with discovered plugin names as keys. Values are
        each a dictionary with the keys 'apps' and 'struct'. The value of 'apps'
        is a list of the web2py applications (in the web2py/applications
        directory) that have files for the given plugin. The value of 'struct'
        is a list of the directories (relative to applications/appname/)
        that are involved in the given plugin. **note** Currently the script
        will sync a maximal version of the directory structure -- i.e., it will
        create and sync any folders present in only some of the plugin versions.
        """
        #get list of all application directories with 'plugin_' in name
        dirfiles = glob.glob('applications/*/*/plugin_*/*')
        dirs = list(set(os.path.dirname(fd) for fd in dirfiles))

        #get list of plugin names
        plugins = list(set(d.split('/')[3] for d in dirs))

        #get list of apps with plugins
        apps = list(set(d.split('/')[1] for d in dirs))

        #get list of plugin directories for each plugin
        pls = {}
        for p in plugins:
            # get all dirs for plugin
            pdirs = [dir for dir in dirs if re.search(p, dir)]
            # get all apps with plugin
            papps = [a for a in apps if
                        [dir for dir in pdirs if re.search(a,dir)]]
            # from pdirs, get unique paths relative to appname
            # TODO: this is hacky -- make it more elegant
            myregex = '/(?=(static|controllers|modules|'
            myregex += 'models|views|tests|private))'
            topdirs = [re.split(myregex, dir)[1] for dir in pdirs]
            filtered_pdirs = [(td + '/' + p) for td in topdirs]

            #get files in other (non-plugin) folders that belong to the plugin
            pstring = 'applications/*/*/' + p + '.*'
            pfiles = list(set(pf for pf in glob.glob(pstring)))
            filtered_pfiles = [(f.split('/')[-2] + '/' + f.split('/')[-1])
                                                            for f in pfiles]

            # separate out dirs by app
            pls[p] = {'apps':papps,
                        'dirs':filtered_pdirs, 'files':filtered_pfiles}

        print 'done getting folders'

        return pls

    def findNewest(self, filename):
        """
        Find the most recently modified version of files with the same name in
        different directories.
        """
        fname = '*/', 'filename'
        flist = glob.glob(fname)
        ftimes = {fpath:os.path.getmtime(fpath) for fpath in flist}


def main():
    mysync = sync()
    mysync.syncit()
    print "All done syncing!"

if __name__ == '__main__':
    main()
