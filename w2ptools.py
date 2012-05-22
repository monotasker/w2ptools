#!/usr/bin/python

import sys
import re
import os
import glob
import pprint
import time
import shutil

"""
w2ptools: A suite of utility scripts designed to simplify working with the
web2py web development framework on a *nix based operating system.

At present w2ptools includes the following classes:

PluginSync: Synchronize versions of a web2py plugin within a single web2py
installation folder.
"""


class PluginSync(object):
    """Synchronize plugins within a single web2py directory"""

    def __init__(self):
        pass

    def sync_all(self):
        """
        Main method for syncing installed versions of module.
        """
        # get information about plugin directories and files
        fs_data = self.fs_data()

        #sync one plugin at a time
        for p in fs_data.keys():
            #find out newest version of each plugin
            #also combines dirs and files from fs_data into single filelist
            newest = self.newest_app(p, fs_data)
            #copy files
            for file in newest['filelist']:
                #copy file to central 'plugins' folder
                self.copy_file(file, ('plugins/%s' % p))
                #copy file from central 'plugins' folder out to other apps
                for app in fs_data[p]['apps']:
                    self.copy_file(file, ('applications/%' % app))

    def copy_file(self, file, newbase):
        #strip 'applications/{appname}/' from file path
        relbits = file.split('/')
        newbits = relbits[2:]
        relfile = '/'.join(newbits)
        #strip filename from relative file path
        relpath = os.path.split(relfile)[0]
        #make new path for file in central plugins folder
        newpath = os.path.join(newbase, newpath)
        #create directories in plugins folder if necessary
        if not os.path.exists(newpath):
            print 'creating directory', newpath
            os.mkdirs(newpath)
        # copy file to central repo
        print 'copying ', file, 'into', newpath
        shutil.copy2(file, os.path.join(newpath, relfile))

    def fs_data(self):
        """
        Return a dictionary with discovered plugin names as keys. Values are
        each a dictionary with the keys 'apps' and 'struct'. The value of
        'apps' is a list of the web2py applications (in the web2py/applications
        directory) that have files for the given plugin. The value of 'dirs'
        is a list of the directories (relative to applications/appname/)
        that are involved in the given plugin.
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
                        [dir for dir in pdirs if re.search(a, dir)]]
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
            pls[p] = {'apps': papps,
                        'dirs': filtered_pdirs, 'files': filtered_pfiles}

        pprint.pprint(pls)
        print 'done getting folders'

        return pls

    def newest_app(self, plugin, fs_data):
        """
        Find the most recently modified version of files with the same name in
        different directories.
        """

        print '\nfinding newest version of ', plugin, '\n'

        apptimes = {}
        for app in fs_data[plugin]['apps']:
            base = os.path.join('applications', app)
            filelist = {}
            for file in fs_data[plugin]['files']:
                fpath = os.path.join(base, file)
                if os.path.exists(fpath):
                    filelist[fpath] = os.path.getmtime(fpath)

            for dr in fs_data[plugin]['dirs']:
                dpath = os.path.join(base, dr)
                if os.path.isdir(dpath):
                    for w in os.walk(dpath):
                        for f in w[2]:
                            fpath = os.path.join(w[0], f)
                            filelist[fpath] = os.path.getmtime(fpath)

            if filelist:
                newest = max(filelist.values())
                newfile = [k for k, v in filelist.iteritems()
                                                    if v == newest][0]
                print 'newest file in ', app, ' = ', newfile, ' ', time.strftime('%c', time.localtime(newest)), '(', newest, ' seconds)'
                apptimes[app] = (newfile, newest, filelist)
            else:
                print 'no file times to compare!'

        maxtime = max(a[1] for a in apptimes.values())
        maxname = [k for k, v in apptimes.iteritems() if v[1] == maxtime][0]

        print maxname.capitalize(), 'seems to have the most recent version ' \
                                            'of the plugin "', plugin, '".'
        resp = raw_input('Is this correct? (Y/n)')
        if resp == 'Y':
            pass
        if resp == 'n':
            print '\navailable versions:'
            for a in fs_data[plugin]['apps']:
                print (fs_data[plugin]['apps'].index(a) + 1), '. ', a
            ovrrd = raw_input('Select the most up-to-date version, or 0 to ' \
                    'skip syncing this plugin: ')
            maxname == fs_data[plugin]['apps'][int(ovrrd) - 1]

        if maxname in fs_data[plugin]['apps']:
            maxfiles = apptimes[maxname][2]
            print 'Syncing plugin ', plugin, 'from app ', maxname
            print 'Plugin files:'
            pprint.pprint(maxfiles)
        elif int(ovrrd) == 0:
            maxname = None
            maxfiles = None
            print 'Skipping syncing plugin ', plugin
        else:
            print 'Something went wrong!'
            pmaxname = None
            maxfiles = None
            print 'Skipping syncing plugin ', plugin

        return {'filelist': maxfiles or None, 'newest_app': maxname or None}


def main():
    mysync = PluginSync()
    mysync.sync_all()
    print "All done syncing!"

if __name__ == '__main__':
    main()
