#!/usr/bin/python

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


class CloneToDir(object):

    """
    Use rsync to clone the contents of a web2py app folder (web2py/applications/<appname>)
    to a folder outside the web2py directory, ignoring .git files.

    This class was motivated by the need to maintain a separate GIT repository
    for the production versions of apps published on fluxflex.com.
    """

    def __init__(self):
        pass

    def clone(self, app, target_path):
        """
        Use rsync to clone the contents of a web2py app folder (web2py/applications/<appname>)
        to a folder outside the web2py directory, ignoring .git files.
        """
        rsync -avz --exclude ".git/*"
        app_path = os.join('applications', app)
        target_path = os.join('../', app, app_path, target_path)


class PluginSync(object):
    """Synchronize plugins within a single web2py directory"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.skiplist = {'plugin_framework':['static/plugin_framework/theme.less']}

    def sync_all(self):
        """
        Main method for syncing installed versions of module.
        """
        # get information about plugin directories and files
        fs_data = self.fs_data()

        #sync one plugin at a time
        for p in fs_data.keys():
            #ask whether user wants to sync this plugin
            choice = raw_input('\nDo you want to sync the plugin ' \
                                    + p + '? Y/n: ')
            if choice == 'Y':
                pass
            elif choice == 'n':
                print 'You have chosen not to sync ', p, '. Continuing. . .'
                continue
            else:
                print 'Sorry, I didn\'nt understand your response. Skipping '\
                        'plugin', p, '. Continuing . . .'
            #find out newest version of each plugin
            #also combines dirs and files from fs_data into single filelist
            newest = self.newest_app(p, fs_data)
            #Stop syncing this plugin if the user sent skip signal in
            #self.newest_app or if that method ran into an error.
            if newest['filelist'] != 'skip':
                #copy files
                for file in newest['filelist']:
                    #skip any files excluded in self.skiplist
                    newest_base = 'applications/' + newest['newest_app'] + '/'
                    filename = file.replace(newest_base, '')
                    if (p in self.skiplist.keys()) and (filename in self.skiplist[p]):
                        print 'skipping file ', file, 'as per settings.'
                    else:
                        #copy file to central 'plugins' folder
                        self.copy_file(file, ('plugins/%s' % p))
                        #copy file from central 'plugins' folder out to other apps
                        for app in fs_data[p]['apps']:
                            if app != newest['newest_app']:
                                self.copy_file(file, ('applications/%s' % app))

    def copy_file(self, file, newbase):
        """
        Copy the selected file to a new directory, preserving the ctime and
        mtime of the original file.
        """
        #strip 'applications/{appname}/' from file path
        relbits = file.split('/')
        newbits = relbits[2:]
        relfile = '/'.join(newbits)
        #strip filename from relative file path
        relpath = os.path.split(relfile)[0]
        #make new path for file in central plugins folder
        newpath = os.path.join(newbase, relpath)
        #create directories in plugins folder if necessary
        if not os.path.exists(newpath):
            print 'creating directory', newpath
            os.makedirs(newpath)
        # copy file to central repo
        if self.verbose:
            print 'copying ', file, 'into', newpath
        shutil.copy2(file, os.path.join(newpath, os.path.split(relfile)[1]))

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
                if self.verbose:
                    print '\nnewest file in the app "', app, '" = '
                    print newfile, ' '
                    print 'last modified on ', time.strftime('%c',
                            time.localtime(newest)), '(', newest, ' seconds)'
                apptimes[app] = (newfile, newest, filelist)
            else:
                print 'no file times to compare!'

        maxtime = max(a[1] for a in apptimes.values())
        maxname = [k for k, v in apptimes.iteritems() if v[1] == maxtime][0]

        print '\n', maxname.capitalize(), 'seems to have the most recent version ' \
                                            'of the plugin "', plugin, '".'
        resp = raw_input('Is this correct? (Y/n)')
        ovrrd = ''
        maxapp = maxname
        if resp == 'Y':
            pass
        elif resp == 'n':
            switch = 0
            while switch < 1:
                print '\navailable versions:'
                for a in fs_data[plugin]['apps']:
                    print (fs_data[plugin]['apps'].index(a) + 1), '. ', a
                ovrrd = raw_input('Select the number for the most up-to-date '\
                        'version, or "n" to skip syncing this plugin: ')
                try:
                    ovrrd = int(ovrrd)
                    if self.verbose == True:
                        print 'ovrrd = ', ovrrd
                        print 'length = ', len(fs_data[plugin]['apps'])
                    if ovrrd in range(1, len(fs_data[plugin]['apps']) + 1):
                        maxapp = fs_data[plugin]['apps'][ovrrd - 1]
                        switch = 1
                    else:
                        print 'Sorry, that didn\'t seem to be a valid option. '\
                            'Try again'
                        switch = 0
                except ValueError:
                    if ovrrd == 'n':
                        switch = 1
                        maxapp = None
                    else:
                        print 'Sorry, that didn\'t seem to be a valid option. '\
                                'Try again'
                        switch = 0

        if maxapp in fs_data[plugin]['apps']:
            maxfiles = apptimes[maxapp][2]
            print 'Syncing plugin ', plugin, 'from app ', maxapp
            if self.verbose == True:
                print 'Plugin files:'
                pprint.pprint(maxfiles)
        elif ovrrd == 'n':
            maxapp = 'skip'
            maxfiles = 'skip'
            print 'Skipping syncing plugin ', plugin
        else:
            print 'Sorry, I didn\'t recognize the information you supplied.'
            maxapp = 'skip'
            maxfiles = 'skip'
            print 'Skipping syncing plugin ', plugin

        return {'filelist': maxfiles, 'newest_app': maxapp}


def main():
    print '\n~~~~~~~~~~~~~~~~~~~'
    print 'Welcome to w2ptools.\n'
    print '\n~~~~~~~~~~~~~~~~~~~'
    counter = 1
    while counter < 5:
        print 'What would you like to do right now?\n'
        print '1. Sync installed plugins between web2py applications'
        print '0. Exit w2ptools\n'
        choice = raw_input('Enter a number to choose an option: ')
        if choice == '1':
            mysync = PluginSync()
            mysync.sync_all()
            print "All done syncing your plugins!"
        elif choice == '0':
            counter = 5
        else:
            if counter == 4:
                print "\nSorry, I seem to be having trouble." \
                        " Let's stop for now.\n"
            else:
                print "\nSorry, I didn't understand your choice." \
                        " Let's try again.\n"
            counter += 1
    print '\nGoodbye!\n'

if __name__ == '__main__':
    main()
