#!/usr/bin/env python
# -*- coding: utf-8 -*-

#############################################################################
##
# This file is part of Taurus
##
# http://taurus-scada.org
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Taurus is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Taurus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
###########################################################################

''' Creates a tree of dirs and restructured text stub files for documenting
the API of a python module with sphinx'''
from __future__ import print_function
from builtins import zip
from builtins import object
import sys
import os
import imp
from jinja2 import Environment, FileSystemLoader


def taurusabspath(*path):
    """A method to determine absolute path for a given relative path to the
    directory where the setup.py script is located"""
    this_dir = os.path.dirname(os.path.abspath(__file__))
    setup_dir = os.path.abspath(os.path.join(this_dir, os.pardir))
    return os.path.join(setup_dir, *path)

# import moduleexplorer from the sources, and without importing taurus
__name = "moduleexplorer"
__path = taurusabspath('lib', 'taurus', 'test', 'moduleexplorer.py')
ModuleExplorer = imp.load_source(__name, __path).ModuleExplorer


class Auto_rst4API_Creator(object):
    AUTOGEN_SIGNATURE = '.. AUTO_RST4API'
    AUTOGEN_MESSAGE = '.. This file was generated by auto_rst4api.py. Changes may be lost'

    def __init__(self, templatespath='./', moduletemplate='api_module.rst', classtemplate='api_class.rst',
                 classindextemplate='api_AllClasses.rst', exclude_patterns=(), verbose=True, overwrite_old=False):
        '''
        :param templates: (str) path to dir where template files are located
        :param moduletemplate: (str) name of the template to be used for module pages
        :param classtemplate: (str) name of the template to be used for class pages
        :param classindextemplate: (str) name of the template to be used for class index page
        :param verbose: (bool) If True (default) status messages will be printed to stdout
        '''

        self.verbose = verbose
        self.exclude_patterns = exclude_patterns

        self.env = Environment(loader=FileSystemLoader(templatespath))
        self.moduletemplate = self.env.get_template(moduletemplate)
        self.classtemplate = self.env.get_template(classtemplate)
        self.classindextemplate = self.env.get_template(classindextemplate)
        self.overwrite_old = overwrite_old

    def _isautogeneratedfile(self, fname):
        ret = False
        f = open(fname, 'r')
        lines = f.readlines()
        for l in lines:
            if l.startswith(self.AUTOGEN_SIGNATURE):
                ret = True
                break
        f.close()

        return ret

    def cleanAutogenerated(self, apipath):
        '''Removes any previously autogenerated rst file in the given path
        or its subdirectories

        :param apipath: (str) directory to clean
        '''
        for dirpath, dirnames, filenames in os.walk(apipath):
            for f in filenames:
                if f.endswith('.rst'):
                    fullname = os.path.join(dirpath, f)
                    try:
                        if self._isautogeneratedfile(fullname):
                            print("Removing %s" % fullname)
                            os.remove(fullname)
                    except Exception as e:
                        print('Error accessing %s:%s' % (fullname, repr(e)))

    def createClassIndex(self, info, ofname):
        '''
        Creates a class index page using the classindextemplate.

        :param info: (dict) dictionary containing the information about the
                     items to document for this module (as generated by
                     :meth:`exploreModule`
        :param ofname: (str) output file name
        '''
        classes = ModuleExplorer.getAll(
            info, 'localclassnames')  # this is a list of tuples of (modulename,class)
        classes = sorted(classes, key=lambda item: item[
                         1])  # sort it by class name
        classes = ['.'.join((m, c))
                   for m, c in classes]  # make a full classname
        if self.verbose:
            print('creating "%s" ...' % ofname, end=' ')
        if not os.path.exists(ofname) or (self.overwrite_old and self._isautogeneratedfile(ofname)):
            text = self.classindextemplate.render(info=info, classes=classes)
            f = open(ofname, "w")
            f.write('\n'.join((self.AUTOGEN_SIGNATURE, self.AUTOGEN_MESSAGE, text)))
            f.close()
            if self.verbose:
                print(' ok.')
        else:
            if self.verbose:
                print(' skipping (file already exists)')

    def createStubs(self, info, docparentpath):
        '''creates rst stub files for modules and classes according to the
        information contained in info.

        :param info: (dict) dictionary containing the information about the
                     items to document for this module (as generated by
                     :meth:`exploreModule`)
        :docparentpath: (str) path to the directory in which the documentation
                        files will be written
        '''
        # create the module doc dir if it didn't exist
        absdocpath = os.path.join(docparentpath, info['basemodulename'])
        if not os.path.exists(absdocpath):
            os.makedirs(absdocpath, mode=0o755)
        # create module index stub in doc parent dir
        ofname = os.path.join(docparentpath, "%s.rst" % info['basemodulename'])
        if self.verbose:
            print('creating "%s" ...' % ofname, end=' ')
        if not os.path.exists(ofname) or (self.overwrite_old and self._isautogeneratedfile(ofname)):
            text = self.moduletemplate.render(info=info)
            f = open(ofname, "w")
            f.write('\n'.join((self.AUTOGEN_SIGNATURE, self.AUTOGEN_MESSAGE, text)))
            f.close()
            if self.verbose:
                print(' ok.')
        else:
            if self.verbose:
                print(' skipping (file already exists)')
        # create class stubs
        for name in info['localclassnames']:
            ofname = os.path.join(absdocpath, "_%s.rst" % name)
            if self.verbose:
                print('creating "%s" ...' % ofname, end=' ')
            if not os.path.exists(ofname) or (self.overwrite_old and self._isautogeneratedfile(ofname)):
                text = self.classtemplate.render(info=info, classname=name)
                f = open(ofname, "w")
                f.write(
                    '\n'.join((self.AUTOGEN_SIGNATURE, self.AUTOGEN_MESSAGE, text)))
                f.close()
                if self.verbose:
                    print(' ok.')
            else:
                if self.verbose:
                    print(' skipping (file already exists)')
        # recurse for submodules
        for sminfo in info['submodules'].values():
            self.createStubs(sminfo, absdocpath)

    def documentModule(self, modulename, docparentpath, exclude_patterns=None):
        '''
        recursive function that walks on the module structure and generates
        documentation files for the given module and its submodules. It also
        creates a class index for the root module

        :param modulename: (str) name of the module to document
        :docparentpath: (str) path to the directory in which the documentation
                        files will be written
        :param exclude_patterns: (seq<str>) sequence of strings containing regexp
                 patterns. Each candidate to be documented will be
                 matched against these patterns and will be excluded
                 if it matches any of them.

        :return: (list<str>) list of warning messages
        '''
        if self.verbose:
            print("\nDocumenting %s..." % modulename)
        if exclude_patterns is None:
            exclude_patterns = self.exclude_patterns
        moduleinfo, w = ModuleExplorer.explore(modulename,
                                               exclude_patterns=exclude_patterns,
                                               verbose=self.verbose)
        self.createStubs(moduleinfo, docparentpath)
        self.createClassIndex(moduleinfo, os.path.join(
            docparentpath, "%s_AllClasses.rst" % modulename))
        if len(w) == 0:
            return []
        else:
            return list(zip(*w))[1]


def main():
    import sys
    if len(sys.argv) != 3:
        print('Usage:\n\t%s modulename docpreffix\n\n' % sys.argv[0])
        sys.exit(1)
    modulename, docparentpath = sys.argv[1:]
    creator = Auto_rst4API_Creator(verbose=True)
    r = creator.documentModule(
        modulename, docparentpath, exclude_patterns=['.*\.test'])
    print('\n\n' + '*' * 50)
    print("Auto Creation of API docs for %s Finished with %i warnings:" % (modulename, len(r)))
    print('\n'.join(r))
    print('*' * 50 + '\n')

if __name__ == "__main__":
    main()
