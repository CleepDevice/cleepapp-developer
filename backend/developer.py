#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import inspect
import importlib
import re
import json
import copy
from zipfile import ZipFile, ZIP_DEFLATED
from tempfile import NamedTemporaryFile
from threading import Thread
from raspiot.raspiot import RaspIotModule
from raspiot.libs.internals.task import Task
from raspiot.libs.internals.console import Console, EndlessConsole
from raspiot.utils import CommandError, MissingParameter, InvalidParameter
from raspiot.libs.internals.installmodule import FRONTEND_DIR, BACKEND_DIR, SCRIPTS_DIR, PATH_FRONTEND, PATH_SCRIPTS
from raspiot.libs.internals import __all__ as internals_libs
from raspiot.libs.externals import __all__ as externals_libs
from raspiot.libs.drivers import __all__ as drivers_libs
from raspiot.libs.configs import __all__ as configs_libs
from raspiot.libs.commands import __all__ as commands_libs
import raspiot.libs.internals.tools as Tools
from raspiot.libs.internals.console import EndlessConsole


__all__ = ['Developer']


class Developer(RaspIotModule):
    """
    Developer module: this module is dedicated only for developers.
    It allows implements and configures remotedev in raspiot ()

    Note:
        https://github.com/tangb/remotedev
    """
    MODULE_AUTHOR = u'Cleep'
    MODULE_VERSION = u'2.0.0'
    MODULE_PRICE = 0
    MODULE_DEPS = []
    MODULE_DESCRIPTION = u'Helps you to develop Cleep applications.'
    MODULE_LONGDESCRIPTION = u'Developer module helps you to develop on Cleep installing \
        and preconfiguring sync tools. It also provides a full page that helps you to \
        check and build your own application.<br/>This module will provide the official way to \
        publish your module on Cleep market.<br/><br/>Lot of resources are available \
        on developer module wiki, have a look and start enjoying Cleep!'
    MODULE_TAGS = [u'developer', u'python', u'cleepos', u'module', 'angularjs', 'cleep', 'cli']
    MODULE_CATEGORY = u'APPLICATION'
    MODULE_COUNTRY = None
    MODULE_URLINFO = u'https://github.com/tangb/cleepmod-developer'
    MODULE_URLHELP = u'https://github.com/tangb/cleepmod-developer/wiki'
    MODULE_URLSITE = None
    MODULE_URLBUGS = u'https://github.com/tangb/cleepmod-developer/issues'

    MODULE_CONFIG_FILE = u'developer.conf'
    DEFAULT_CONFIG = {
        u'moduleindev': None
    }

    CLI = u'/usr/local/bin/cleep-cli'
    CLI_WATCHER_CMD = u'%s watch --loglevel=40' % CLI
    CLI_TESTS_CMD = u'%s modtest --module "%s" --coverage'
    CLI_TESTS_COV_CMD = u'%s modtestcov --module "%s" --missing'
    CLI_NEW_APPLICATION_CMD = u'%s modcreate --module "%s"'
    CLI_DOCS_CMD = u'%s moddocs --module "%s"'

    FRONT_FILE_TYPE_DROP = u'Do not include file'
    FRONT_FILE_TYPE_SERVICE_JS = u'service-js'
    FRONT_FILE_TYPE_WIDGET_JS = u'widget-js'
    FRONT_FILE_TYPE_WIDGET_HTML = u'widget-html'
    FRONT_FILE_TYPE_WIDGET_CSS = u'widget-css'
    FRONT_FILE_TYPE_CONFIG_JS = u'config-js'
    FRONT_FILE_TYPE_CONFIG_HTML = u'config-html'
    FRONT_FILE_TYPE_CONFIG_CSS = u'config-css'
    FRONT_FILE_TYPE_RESOURCE = u'resource'
    FRONT_FILE_TYPES = [FRONT_FILE_TYPE_DROP, FRONT_FILE_TYPE_SERVICE_JS, FRONT_FILE_TYPE_WIDGET_JS, FRONT_FILE_TYPE_WIDGET_HTML, FRONT_FILE_TYPE_WIDGET_CSS, FRONT_FILE_TYPE_CONFIG_JS, FRONT_FILE_TYPE_CONFIG_HTML, FRONT_FILE_TYPE_CONFIG_CSS, FRONT_FILE_TYPE_RESOURCE]

    CATEGORY_APPLICATION = u'APPLICATION'
    CATEGORY_MOBILE = u'MOBILE'
    CATEGORY_DRIVER = u'DRIVER'
    CATEGORY_HOMEAUTOMATION = u'HOMEAUTOMATION'
    CATEGORY_MEDIA = u'MEDIA'
    CATEGORY_SERVICE = u'SERVICE'
    CATEGORIES = [CATEGORY_APPLICATION, CATEGORY_MOBILE, CATEGORY_DRIVER, CATEGORY_HOMEAUTOMATION, CATEGORY_MEDIA, CATEGORY_SERVICE]

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled (bool): flag to set debug level to logger
        """
        #init
        RaspIotModule.__init__(self, bootstrap, debug_enabled)

        #members
        self.__developer_uuid = None
        self.raspiot_path = os.path.dirname(inspect.getfile(RaspIotModule))
        self.__module_name = None
        self.__module_archive = None
        self.__module_version = None
        self.__watcher_task = None
        self.__tests_running = False
        self.__tests = None
        self.__docs_running = False
        self.__docs = None

        #events
        self.frontend_restart_event = self._get_event('developer.frontend.restart')
        self.tests_output_event = self._get_event('developer.tests.output')
        self.docs_output_event = self._get_event('developer.docs.output')

    def _configure(self):
        """
        Configure module
        """
        #add dummy device
        self.logger.debug('device_count=%d' % self._get_device_count())
        if self._get_device_count()==0:
            self.logger.debug(u'Add default devices')
            developer = {
                u'type': 'developer',
                u'name': 'Developer'
            }
            self._add_device(developer)

        #store device uuids for events
        devices = self.get_module_devices()
        self.logger.debug('devices: %s' % devices)
        for uuid in devices:
            if devices[uuid][u'type']==u'developer':
                self.__developer_uuid = uuid

        #start watcher task
        self.__launch_watcher()

    def __launch_watcher(self):
        """
        Launch cleep-cli watch command
        """
        self.logger.info(u'Launch watcher task')
        self.__watcher_task = EndlessConsole(self.CLI_WATCHER_CMD, self.__watcher_callback, self.__watcher_end_callback)
        self.__watcher_task.start()

    def __watcher_callback(self, stdout, stderr):
        """
        Callback when watcher receives messages on stdXXX

        Args:
            stdout (string): message from stdout
            stderr (string): message from stderr
        """
        if self.__watcher_task:
            self.logger.error('Error on watcher: %s %s' % (stdout, stderr))

    def __watcher_end_callback(self, return_code, killed):
        """
        Callback when watcher task ends

        Args:
            return_code (int): command return code
            killed (bool): True if watcher killed
        """
        if self.__watcher_task:
            self.logger.error('Watcher stops while it should not with return code "%s" (killed? %s)' % (return_code, killed))

        #start new instance
        self.__launch_watcher()

    def get_module_devices(self):
        """
        Return module devices
        """
        devices = super(Developer, self).get_module_devices()
        data = {}
        self.__developer_uuid = devices.keys()[0]
        devices[self.__developer_uuid].update(data)

        return devices

    def _stop(self):
        """
        Custom stop: stop remotedev thread
        """
        if self.__watcher_task:
            self.__watcher_task.stop()
        if self.__tests:
            self.__tests.stop()
        if self.__docs:
            self.__docs.stop()

    def set_module_in_development(self, module_name):
        """
        Set module in development. It save in config the module, and enable debug.
        It also disable debug on old module in debug if any.

        Args:
            module_name (string): module to enable development on
        """
        #disable debug on old module
        old_module = self._get_config_field(u'moduleindev')
        if old_module:
            try:
                #module may not exist
                if old_module==u'developer':
                    self.set_debug(False)
                elif len(old_module)>0:
                    self.send_command(u'set_module_debug', u'system', {u'module': old_module, u'debug': False})
            except:
                pass
            
        #save new module in dev
        self._set_config_field(u'moduleindev', module_name)
        if module_name==u'developer':
            self.set_debug(True)
        elif len(module_name)>0:
            self.send_command(u'set_module_debug', u'system', {u'module': module_name, u'debug': True})

    def restart_frontend(self):
        """
        Send event to restart frontend
        """
        self.logger.info(u'Sending restart event to frontend')
        self.frontend_restart_event.send(to=u'rpc')

    def create_application(self, module_name):
        """
        Create new application skel

        Args:
            module_name (string): module name
        """
        cmd = self.CLI_NEW_APPLICATION_CMD % (self.CLI, module_name)
        self.logger.debug(u'Create app cmd: %s' % cmd)

        c = Console()
        res = c.command(cmd, 10.0)
        self.logger.info('Create app cmd result: %s %s' % (res['stdout'], res['stderr']))
        if res['error'] or res['killed'] or c.get_last_return_code()!=0:
            raise CommandError(u'Error during application creation. Consult the logs.')

        return True

    def __analyze_module_python(self, module_name):
        """
        Analyze package python part

        Args:
            module_name (string): module name

        Return:
            dict: python package data::
                {
                    metadata (dict): module metadata,
                    files (list): list of python files (libs, module...)
                }
        """
        #init
        errors = []
        warnings = []
        self.logger.debug(u'Raspiot_path=%s' % self.raspiot_path)
        modules_path = os.path.join(self.raspiot_path, u'modules')

        #get module instance
        try:
            module_ = importlib.import_module(u'raspiot.modules.%s.%s' % (module_name, module_name))
            class_ = getattr(module_, module_name.capitalize())
        except:
            self.logger.exception(u'Unable to load module "%s". Please check your code' % module_name) 
            raise InvalidParameter(u'Unable to load module "%s". Please check your code' % module_name)

        #check module metadata
        #MODULE_DESCRIPTION
        if not hasattr(class_, u'MODULE_DESCRIPTION'):
            errors.append(u'Mandatory field MODULE_DESCRIPTION is missing')
        elif not isinstance(getattr(class_, u'MODULE_DESCRIPTION'), unicode):
            errors.append(u'Field MODULE_DESCRIPTION must be an unicode string')
        elif len(getattr(class_, u'MODULE_DESCRIPTION'))==0:
            errors.append(u'Field MODULE_DESCRIPTION must be provided')
        #MODULE_LONGDESCRIPTION
        if not hasattr(class_, u'MODULE_LONGDESCRIPTION'):
            errors.append(u'Mandatory field MODULE_LONGDESCRIPTION is missing')
        elif not isinstance(getattr(class_, u'MODULE_LONGDESCRIPTION'), unicode):
            errors.append(u'Field MODULE_LONGDESCRIPTION must be an unicode string')
        elif len(getattr(class_, u'MODULE_LONGDESCRIPTION'))==0:
            errors.append(u'Field MODULE_LONGDESCRIPTION must be provided')
        #MODULE_CATEGORY
        if not hasattr(class_, u'MODULE_CATEGORY'):
            errors.append(u'Mandatory field MODULE_CATEGORY is missing')
        elif not isinstance(getattr(class_, u'MODULE_CATEGORY'), unicode):
            errors.append(u'Field MODULE_CATEGORY must be an unicode string')
        elif len(getattr(class_, u'MODULE_CATEGORY'))==0:
            errors.append(u'Field MODULE_CATEGORY must be provided')
        elif getattr(class_, u'MODULE_CATEGORY') not in self.CATEGORIES:
            errors.append(u'Field MODULE_CATEGORY must be one of possible values (see doc)')
        #MODULE_DEPS
        if not hasattr(class_, u'MODULE_DEPS'):
            errors.append(u'Mandatory field MODULE_DEPS is missing')
        elif hasattr(class_, u'MODULE_DEPS') and not isinstance(getattr(class_, u'MODULE_DEPS'), list):
            errors.append(u'Field MODULE_DEPS must be a list')
        #MODULE_VERSION
        version_pattern = re.compile('\d+\.\d+\.\d+')
        if not hasattr(class_, u'MODULE_VERSION'):
            errors.append(u'Mandatory field MODULE_VERSION is missing')
        elif not isinstance(getattr(class_, u'MODULE_VERSION'), unicode):
            errors.append(u'Field MODULE_VERSION must be an unicode string')
        elif len(getattr(class_, u'MODULE_VERSION'))==0:
            errors.append(u'Field MODULE_VERSION must be provided')
        elif version_pattern.match(getattr(class_, u'MODULE_VERSION')) is None:
            errors.append(u'Field MODULE_VERSION must match this format <number>.<number>.<number>')
        #MODULE_TAGS
        if not hasattr(class_, u'MODULE_TAGS'):
            errors.append(u'Mandatory field MODULE_TAGS is missing')
        elif not isinstance(getattr(class_, u'MODULE_TAGS'), list):
            errors.append(u'Field MODULE_TAGS must be a list')
        elif len(getattr(class_, u'MODULE_TAGS'))==0:
            warnings.append('Field MODULE_TAGS should contains strings to help finding your module')
        #MODULE_URLINFO
        if not hasattr(class_, u'MODULE_URLINFO'):
            errors.append(u'Mandatory field MODULE_URLINFO is missing')
        elif not isinstance(getattr(class_, u'MODULE_URLINFO'), unicode) and getattr(class_, u'MODULE_URLINFO') is not None:
            errors.append(u'Field MODULE_URLINFO must be an unicode string or None')
        elif getattr(class_, u'MODULE_URLINFO') is None or len(getattr(class_, u'MODULE_URLINFO'))==0:
            warnings.append('Field MODULE_URLINFO should be filled with url that describes your module')
        #MODULE_URLHELP
        if not hasattr(class_, u'MODULE_URLHELP'):
            errors.append(u'Mandatory field MODULE_URLHELP is missing')
        elif not isinstance(getattr(class_, u'MODULE_URLHELP'), unicode) and getattr(class_, u'MODULE_URLHELP') is not None:
            errors.append(u'Field MODULE_URLHELP must be an unicode string or None')
        elif getattr(class_, u'MODULE_URLHELP') is None or len(getattr(class_, u'MODULE_URLHELP'))==0:
            warnings.append('Field MODULE_URLHELP should be filled with url that gives access to your module support page')
        #MODULE_URLSITE
        if not hasattr(class_, u'MODULE_URLSITE'):
            errors.append(u'Mandatory field MODULE_URLSITE is missing')
        elif not isinstance(getattr(class_, u'MODULE_URLSITE'), unicode) and getattr(class_, u'MODULE_URLSITE') is not None:
            errors.append(u'Field MODULE_URLSITE must be an unicode string or None')
        elif getattr(class_, u'MODULE_URLSITE') is None or len(getattr(class_, u'MODULE_URLSITE'))==0:
            warnings.append('Field MODULE_URLSITE should be filled with module website url')
        #MODULE_URLBUGS
        if not hasattr(class_, u'MODULE_URLBUGS'):
            errors.append(u'Mandatory field MODULE_URLBUGS is missing')
        elif not isinstance(getattr(class_, u'MODULE_URLBUGS'), unicode) and getattr(class_, u'MODULE_URLBUGS') is not None:
            errors.append(u'Field MODULE_URLBUGS must be an unicode string or None')
        elif getattr(class_, u'MODULE_URLBUGS') is None or len(getattr(class_, u'MODULE_URLBUGS'))==0:
            warnings.append('Field MODULE_URLBUGS should be filled with module bugs tracking system url')
        #MODULE_COUNTRY
        if not hasattr(class_, u'MODULE_COUNTRY'):
            errors.append(u'Mandatory field MODULE_COUNTRY is missing')
        elif not isinstance(getattr(class_, u'MODULE_COUNTRY'), unicode) and getattr(class_, u'MODULE_COUNTRY') is not None:
            errors.append(u'Field MODULE_COUNTRY must be an unicode string or None')

        #build package metadata
        description = getattr(class_, u'MODULE_DESCRIPTION', u'')
        longdescription = getattr(class_, u'MODULE_LONGDESCRIPTION', u'')
        category = getattr(class_, u'MODULE_CATEGORY', u'')
        deps = getattr(class_, u'MODULE_DEPS', [])
        version = getattr(class_, u'MODULE_VERSION', u'')
        tags = getattr(class_, u'MODULE_TAGS', [])
        urls = {
            u'info': None,
            u'help': None,
            u'bugs': None,
            u'site': None
        }
        urls[u'info'] = getattr(class_, u'MODULE_URLINFO', u'')
        urls[u'help'] = getattr(class_, u'MODULE_URLHELP', u'')
        urls[u'site'] = getattr(class_, u'MODULE_URLSITE', u'')
        urls[u'bugs'] = getattr(class_, u'MODULE_URLBUGS', u'')
        country = getattr(class_, u'MODULE_COUNTRY', u'')
        price = getattr(class_, u'MODULE_PRICE', 0)
        author = getattr(class_, u'MODULE_AUTHOR', u'')
        metadata = {
            u'description': description,
            u'longdescription': longdescription,
            u'category': category,
            u'deps': deps,
            u'version': version,
            u'tags': tags,
            u'country': country,
            u'urls': urls,
            u'price': price,
            u'author': author
        }
        self.logger.debug('Module "%s" metadata: %s' % (module_name, metadata))

        #add main module file
        files = {
            u'module': None,
            u'libs': []
        }
        module_main_fullpath = inspect.getfile(module_).replace(u'.pyc', u'.py')
        (module_path, module_main_filename) = os.path.split(module_main_fullpath)
        files['module'] = {
            u'fullpath': module_main_fullpath,
            u'path': module_main_fullpath.replace(modules_path, u'')[1:],
            u'filename': module_main_filename
        }
        self.logger.debug('Main module file: %s' % module_main_fullpath)

        #get all files to package
        paths = []
        for root, _, filenames in os.walk(module_path):
            for filename in filenames:
                fullpath = os.path.join(root, filename)
                (file_no_ext, ext) = os.path.splitext(filename)
                if not file_no_ext.lower().endswith(u'formatter') and not file_no_ext.lower().endswith(u'event') \
                    and filename not in (module_main_filename) and ext==u'.py':
                    self.logger.debug('File to import: %s' % fullpath)
                    paths.append(os.path.split(fullpath)[0])
                    files[u'libs'].append({
                        u'fullpath': fullpath,
                        u'path': fullpath.replace(modules_path, u'')[1:],
                        u'filename': os.path.basename(fullpath),
                        u'selected': True
                    })
                    
        #check missing __init__.py
        init_py_path = os.path.join(module_path, u'__init__.py')
        if not os.path.exists(init_py_path):
            errors.append(u'Mandatory file "%s" is missing. Please add empty file. More infos <a href="https://docs.python.org/2.7/tutorial/modules.html#packages" target="_blank">here</a>.' % init_py_path)
        for path in paths:
            init_py_path = os.path.join(path, u'__init__.py')
            if not os.path.exists(init_py_path):
                errors.append(u'Mandatory file "%s" is missing. Please add empty file. More infos <a href="https://docs.python.org/2.7/tutorial/modules.html#packages" target="_blank">here</a>.' % init_py_path)
            
        #get events
        events = []
        for f in os.listdir(module_path):
            fullpath = os.path.join(module_path, f)
            (event, ext) = os.path.splitext(f)
            parts = Tools.full_path_split(fullpath)
            if event.lower().find(u'event')>=0 and ext==u'.py':
                self.logger.debug('Loading event "%s"' % u'raspiot.modules.%s.%s' % (parts[-2], event))
                try:
                    mod_ = importlib.import_module(u'raspiot.modules.%s.%s' % (parts[-2], event))
                    event_class_name = next((item for item in dir(mod_) if item.lower()==event.lower()), None)
                    if event_class_name:
                        class_ = getattr(mod_, event_class_name)
                        events.append({
                            u'fullpath': fullpath,
                            u'path': u'%s.py' % os.path.join(parts[-2], event),
                            u'filename': os.path.basename(fullpath),
                            u'name': event_class_name,
                            u'selected': True
                        })
                    else:
                        self.logger.debug(u'Event class must have the same name than filename (%s)' % f)
                        errors.append(u'Event class must have the same name than filename (%s)' % f)
                except:
                    self.logger.exception(u'Unable to load event %s' % f)
                    errors.append(u'Unable to load event %s' % f)

        #get formatters
        formatters = []
        for f in os.listdir(module_path):
            fullpath = os.path.join(module_path, f)
            (formatter, ext) = os.path.splitext(f)
            parts = Tools.full_path_split(fullpath)
            if formatter.lower().find(u'formatter')>=0 and ext==u'.py':
                self.logger.debug('Loading formatter "%s"' % u'raspiot.modules.%s.%s' % (parts[-2], formatter))
                try:
                    mod_ = importlib.import_module(u'raspiot.modules.%s.%s' % (parts[-2], formatter))
                    formatter_class_name = next((item for item in dir(mod_) if item.lower()==formatter.lower()), None)
                    if formatter_class_name:
                        class_ = getattr(mod_, formatter_class_name)
                        formatters.append({
                            u'fullpath': fullpath,
                            u'path': u'%s.py' % os.path.join(parts[-2], formatter),
                            u'filename': os.path.basename(fullpath),
                            u'name': formatter_class_name,
                            u'selected': True
                        })
                    else:
                        self.logger.debug(u'Formatter class must have the same name than filename (%s)' % f)
                        errors.append(u'Formatter class must have the same name than filename (%s)' % f)
                except:
                    self.logger.exception(u'Unable to load formatter %s' % f)
                    errors.append(u'Unable to load formatter %s' % f)

        return {
            u'data': {
                u'files': files,
                u'events': events,
                u'formatters': formatters,
                u'errors': errors,
                u'warnings': warnings
            },
            u'metadata': metadata,
        }

    def __fill_js_file_types(self, files, desc_json):
        """
        Fill file types as well as possible
        """
        #use desc.json content if possible
        if desc_json:
            #set widget-js and service-js
            if u'global' in desc_json and u'js' in desc_json[u'global']:
                for key in desc_json[u'global'][u'js']:
                    if key not in files:
                        continue
                    if key.find('.service.js')>=0:
                        files[key][u'type'] = self.FRONT_FILE_TYPE_SERVICE_JS
                    else:
                        files[key][u'type'] = self.FRONT_FILE_TYPE_WIDGET_JS

            #set widget-html
            if u'global' in desc_json and u'html' in desc_json[u'global']:
                for key in desc_json[u'global'][u'html']:
                    if key in files:
                        files[key][u'type'] = self.FRONT_FILE_TYPE_WIDGET_HTML

            #set widget-css
            if u'global' in desc_json and u'css' in desc_json[u'global']:
                for key in desc_json[u'global'][u'css']:
                    if key in files:
                        files[key][u'type'] = self.FRONT_FILE_TYPE_WIDGET_CSS

            #set config-js
            if u'config' in desc_json and u'js' in desc_json[u'config']:
                for key in desc_json[u'config'][u'js']:
                    if key in files:
                        files[key][u'type'] = self.FRONT_FILE_TYPE_CONFIG_JS

            #set config-html
            if u'config' in desc_json and u'html' in desc_json[u'config']:
                for key in desc_json[u'config'][u'html']:
                    if key in files:
                        files[key][u'type'] = self.FRONT_FILE_TYPE_CONFIG_HTML

            #set config-css
            if u'config' in desc_json and u'css' in desc_json[u'config']:
                for key in desc_json[u'config'][u'css']:
                    if key in files:
                        files[key][u'type'] = self.FRONT_FILE_TYPE_CONFIG_CSS

            if u'res' in desc_json:
                for key in desc_json[u'res']:
                    if key in files:
                        files[key][u'type'] = self.FRONT_FILE_TYPE_RESOURCE

        else:
            #no desc.json file, try to guess empty types
            for key in files:
                if key==u'icon':
                    #icon field, drop
                    continue
                if files[key][u'type']!=self.FRONT_FILE_TYPE_DROP:
                    #drop already found type
                    continue

                #try to identify file type
                if key.find(u'.service.js')>0:
                    files[key][u'type'] = self.FRONT_FILE_TYPE_SERVICE_JS
                elif key.find(u'.directive.js')>0:
                    files[key][u'type'] = self.FRONT_FILE_TYPE_CONFIG_JS
                elif key.find(u'.directive.html')>0:
                    files[key][u'type'] = self.FRONT_FILE_TYPE_CONFIG_HTML
                elif key.find(u'.directive.css')>0:
                    files[key][u'type'] = self.FRONT_FILE_TYPE_CONFIG_CSS
                elif key.find(u'.widget.js')>0:
                    files[key][u'type'] = self.FRONT_FILE_TYPE_WIDGET_JS
                elif key.find(u'.widget.html')>0:
                    files[key][u'type'] = self.FRONT_FILE_TYPE_WIDGET_HTML
                elif key.find(u'.widget.css')>0:
                    files[key][u'type'] = self.FRONT_FILE_TYPE_WIDGET_CSS
                elif files[key][u'ext'] in (u'png', u'jpg', u'jpeg', u'gif'):
                    files[key][u'type'] = self.FRONT_FILE_TYPE_RESOURCE
                elif key==u'desc.json':
                    files[key][u'type'] = self.FRONT_FILE_TYPE_RESOURCE

        return files

    def __check_mdimgsrc_directive(self, js_files):
        """
        Check if developer uses md-img-src directive to display its images

        Args:
            js_files (dict): dict of js files
          
        Returns:
            list: list of warnings
        """
        #init
        images = []
        htmls = []
        cacheds = []
        warnings = []

        #get images
        for js_file in js_files:
            ext = js_files[js_file][u'ext'].lower()
            if ext in (u'jpg', u'jpeg', u'png', u'gif'):
                images.append(js_files[js_file])
            if ext in (u'html'):
                htmls.append(js_files[js_file])

        #no image, no need to go further
        if len(images)==0:
            return warnings

        #cache html files content
        for html in htmls:
            fd = self.cleep_filesystem.open(html[u'fullpath'], u'r')
            cacheds.append(u'\n'.join(fd.readlines()))
            self.cleep_filesystem.close(fd)

        #check directive usage for found images
        for image in images:
            pattern = r"mod-img-src\s*=\s*[\"']\s*%s\s*[\"']" % image[u'path']
            self.logger.debug(u'Mod-img-src pattern: %s' % pattern)
            found = False
            for cached in cacheds:
                matches = re.finditer(pattern, cached, re.MULTILINE)
                if len(list(matches))>0:
                    found = True
            if not found:
                warnings.append(u'Image "%s" may not be displayed properly because mod-img-src directive wasn\'t used' % image[u'filename'])

        return warnings

    def __analyze_module_js(self, module_name):
        """
       Analyze module js part

        Args:
            module_name (string): module name

        Returns:
            tuple (dict, string): js data adn changelog
        """
        errors = []
        warnings = []

        #iterate over files in supposed js module directory
        all_files = {}
        module_path = os.path.join(PATH_FRONTEND, u'js/modules/', module_name)
        self.logger.info('module_path=%s' % module_path)
        if not os.path.exists(module_path):
            raise CommandError(u'Module "%s" has no javascript' % module_path)
        for root, _, filenames in os.walk(module_path):
            for f in filenames:
                self.logger.info('root=%s f=%s' % (root, f))
                #drop some files
                if f.startswith(u'.') or f.startswith(u'~') or f.endswith(u'.tmp'):
                    continue

                #get file values
                fullpath = os.path.join(root, f)
                filepath = os.path.join(root.replace(module_path, u''), f)
                if filepath[0]==os.path.sep:
                    filepath = filepath[1:]
                filename = f

                #mandatory field
                mandatory = False
                type_ = self.FRONT_FILE_TYPE_DROP
                if filename==u'desc.json':
                    mandatory = True
                    type_ = self.FRONT_FILE_TYPE_RESOURCE

                #append file infos
                all_files[filepath] = {
                    u'fullpath': fullpath,
                    u'path': filepath,
                    u'filename': filename,
                    u'ext': os.path.splitext(fullpath)[1].replace(u'.', u''),
                    u'mandatory': mandatory,
                    u'type': type_
                }
        self.logger.debug('all_files: %s' % all_files)

        #load existing description file
        desc_json = u''
        desc_json_path = os.path.join(PATH_FRONTEND, u'js/modules/', module_name, u'desc.json')
        self.logger.debug(u'desc.json path: %s' % desc_json_path)
        if os.path.exists(desc_json_path):
            desc_json = self.cleep_filesystem.read_json(desc_json_path)

        #fill file types if possible
        all_files = self.__fill_js_file_types(all_files, desc_json)
        
        #fill changelog
        changelog = u''
        if desc_json and u'changelog' in desc_json:
            changelog = desc_json[u'changelog']

        #set icon
        icon = u'bookmark'
        if desc_json and u'icon' in desc_json:
            icon = desc_json[u'icon']

        #check usage of mod-img-src directive in front source code
        warnings = self.__check_mdimgsrc_directive(all_files)

        return {
            u'data': {
                u'files': all_files.values(),
                u'filetypes': self.FRONT_FILE_TYPES,
                u'errors': errors,
                u'warnings': warnings
            },
            u'icon': icon,
            u'changelog': changelog
        }

    def __analyze_scripts(self, module_name):
        """
        Analyze scripts for specified module

        Args:
            module_name (string): module name to search scripts for

        Returns:
            tuple (dict, string): js data adn changelog
        """
        script_preinst = os.path.join(PATH_SCRIPTS, module_name, u'preinst.sh')
        script_postinst = os.path.join(PATH_SCRIPTS, module_name, u'postinst.sh')
        script_preuninst = os.path.join(PATH_SCRIPTS, module_name, u'preuninst.sh')
        script_postuninst = os.path.join(PATH_SCRIPTS, module_name, u'postuninst.sh')

        return {
            u'preinst': {
                u'found': os.path.exists(script_preinst),
                u'fullpath': script_preinst
            },
            u'postinst': {
                u'found': os.path.exists(script_postinst),
                u'fullpath': script_postinst
            },
            u'preuninst': {
                u'found': os.path.exists(script_preuninst),
                u'fullpath': script_preuninst
            },
            u'postuninst': {
                u'found': os.path.exists(script_postuninst),
                u'fullpath': script_postuninst
            }
        }

    def analyze_module(self, module_name):
        """
        Analyze specified module package and return archive name and filename to download it

        Args:
            module_name (string): module name

        Returns:
            dict: archive infos::
                {
                    url (string): archive url,
                    name (string): archive name (usually name of module)
                }
        """
        #check parameters
        if module_name is None or len(module_name)==0:
            raise MissingParameter(u'Parameter "module_name" is missing')
        module_path = os.path.join(self.raspiot_path, u'modules', module_name, u'%s.py' % module_name)
        if not os.path.exists(module_path):
            raise InvalidParameter(u'Module "%s" does not exist' % module_name)

        #analyze python part
        analyze_python = self.__analyze_module_python(module_name)

        #analyze front part
        analyze_js = self.__analyze_module_js(module_name)

        #analyze scripts part
        analyze_scripts = self.__analyze_scripts(module_name)

        return {
            u'python': analyze_python[u'data'],
            u'js': analyze_js[u'data'],
            u'scripts': analyze_scripts,
            u'changelog': analyze_js[u'changelog'],
            u'icon': analyze_js[u'icon'],
            u'metadata': analyze_python[u'metadata']
        }

    def generate_desc_json(self, js_files, icon):
        """
        Generate desc.json file inside module directory

        Args:
            js_files (dict): js.files part of data returned by analyze_module command
            icon (string): module icon string

        Return:
            bool: True if file generated successfully
        """
        content = {
            u'icon': icon,
            u'global': {
                u'js': [],
                u'html': [],
                u'css': []
            },
            u'config': {
                u'js': [],
                u'html': [],
                u'css': []
            },
            u'res': []
        }
        
        #iterates over files
        for f in js_files:
            if f[u'type']==self.FRONT_FILE_TYPE_SERVICE_JS:
                content[u'global'][u'js'].append(f[u'path'])
            elif f[u'type']==self.FRONT_FILE_TYPE_WIDGET_JS:
                content[u'global'][u'js'].append(f[u'path'])
            elif f[u'type']==self.FRONT_FILE_TYPE_WIDGET_HTML:
                content[u'global'][u'html'].append(f[u'path'])
            elif f[u'type']==self.FRONT_FILE_TYPE_WIDGET_CSS:
                content[u'global'][u'css'].append(f[u'path'])
            elif f[u'type']==self.FRONT_FILE_TYPE_CONFIG_JS:
                content[u'config'][u'js'].append(f[u'path'])
            elif f[u'type']==self.FRONT_FILE_TYPE_CONFIG_HTML:
                content[u'config'][u'html'].append(f[u'path'])
            elif f[u'type']==self.FRONT_FILE_TYPE_CONFIG_CSS:
                content[u'config'][u'css'].append(f[u'path'])
            elif f[u'type']==self.FRONT_FILE_TYPE_RESOURCE:
                content[u'res'].append(f[u'path'])
        self.logger.debug(u'Generated desc.json content: %s' % content)

        #write json file to js module directory
        if len(js_files)>0:
            js_path = os.path.join(js_files[0][u'fullpath'].replace(js_files[0][u'path'], u''), u'desc.json')
            self.logger.debug(u'js_path=%s' % js_path)
            return self.cleep_filesystem.write_json(js_path, content)
            
        else:
            self.logger.warning(u'Nothing to write to desc.json file')
            return False

    def build_package(self, module_name, data):
        """
        Build module package archive in zip format.
        Archive is not protected by password

        Args:
            module_name (string): module name
            data (dict): data returned by analyze_module command

        Return:
            string: url of archive to download or None if error occured
        """
        #init
        self.__module_archive = None
        self.__module_name = None
        self.__module_version = None

        #build desc.json
        if not self.generate_desc_json(data[u'js'][u'files'], data[u'icon']):
            raise CommandError(u'Unable to generate desc.json file. Please check logs and sent data')

        #build module description file (module.json)
        fd = NamedTemporaryFile(delete=False)
        module_json = fd.name
        metadata = copy.deepcopy(data[u'metadata'])
        metadata[u'icon'] = data[u'icon']
        metadata[u'changelog'] = data[u'changelog']
        fd.write(json.dumps(metadata))
        fd.close()

        #build zip archive
        fd = NamedTemporaryFile(delete=False)
        module_archive = fd.name
        self.logger.debug('Archive filepath: %s' % module_archive)
        archive = ZipFile(fd, u'w', ZIP_DEFLATED)

        #add js files
        for f in data[u'js'][u'files']:
            if f[u'type']!=self.FRONT_FILE_TYPE_DROP:
                archive.write(f[u'fullpath'], os.path.join(FRONTEND_DIR, u'js', u'modules', module_name, f['path']))

        #add python files
        path_in = data[u'python'][u'files'][u'module'][u'fullpath']
        path_out = os.path.join(BACKEND_DIR, u'modules', data[u'python'][u'files'][u'module'][u'path'])
        archive.write(path_in, path_out)
        for f in data[u'python'][u'files'][u'libs']:
            if f[u'selected']:
                path_in = f[u'fullpath']
                path_out = os.path.join(BACKEND_DIR, u'modules', f[u'path'])
                archive.write(path_in, path_out)
        for f in data[u'python'][u'events']:
            if f[u'selected']:
                path_in = f[u'fullpath']
                path_out = os.path.join(BACKEND_DIR, u'modules', f[u'path'])
                archive.write(path_in, path_out)
        for f in data[u'python'][u'formatters']:
            if f[u'selected']:
                path_in = f[u'fullpath']
                path_out = os.path.join(BACKEND_DIR, u'modules', f[u'path'])
                archive.write(path_in, path_out)

        #add scripts
        if data[u'scripts'][u'preinst'][u'found']:
            archive.write(data[u'scripts'][u'preinst'][u'fullpath'], os.path.join(SCRIPTS_DIR, u'preinst.sh'))
        if data[u'scripts'][u'postinst'][u'found']:
            archive.write(data[u'scripts'][u'postinst'][u'fullpath'], os.path.join(SCRIPTS_DIR, u'postinst.sh'))
        if data[u'scripts'][u'preuninst'][u'found']:
            archive.write(data[u'scripts'][u'preuninst'][u'fullpath'], os.path.join(SCRIPTS_DIR, u'preuninst.sh'))
        if data[u'scripts'][u'postuninst'][u'found']:
            archive.write(data[u'scripts'][u'postuninst'][u'fullpath'], os.path.join(SCRIPTS_DIR, u'postuninst.sh'))

        #add module.json
        archive.write(module_json, u'module.json')

        #close archive
        archive.close()

        #clean some stuff
        if os.path.exists(module_json):
            os.remove(module_json)

        #save now related package infos to make sure everything is completed successfully
        self.__module_archive = module_archive
        self.__module_name = module_name
        self.__module_version = data[u'metadata'][u'version']

        return True

    def download_package(self):
        """
        Download latest generated package

        Returns:
            dict: archive infos::

                {
                    data: filepath
                    filename: new filename
                }

        """
        self.logger.debug(u'Download package')
        if self.__module_name is None or self.__module_archive is None or self.__module_version is None:
            raise CommandError(u'No module package generated')

        return {
            u'filepath': self.__module_archive,
            u'filename': u'cleepmod_%s_%s.zip' % (self.__module_name, self.__module_version)
        }

    def __tests_callback(self, stdout, stderr):
        """
        Tests cli outputs

        Args:
            stdout (string): stdout message
            stderr (string): stderr message
        """
        message = (stdout if stdout is not None else '') + (stderr if stderr is not None else '')
        self.logger.info(u'Receive tests cmd message: "%s"' % message)
        self.tests_output_event.send(params={u'message': message}, render=False)

    def __tests_end_callback(self, return_code, killed):
        """
        Tests cli ended

        Args:
            return_code (int): command return code
            killed (bool): True if command killed
        """
        self.logger.info(u'Tests command terminated with return code "%s" (killed=%s)' % (return_code, killed))
        self.__tests_running = False

    def launch_tests(self, module_name):
        """
        Launch unit tests

        Args:
            module_name (string): module name
        """
        if self.__tests_running:
            raise CommandError(u'Tests are already running')

        cmd = self.CLI_TESTS_CMD % (self.CLI, module_name)
        self.logger.debug(u'Test cmd: %s' % cmd)
        self.__tests = EndlessConsole(cmd, self.__tests_callback, self.__tests_end_callback)
        self.__tests_running = True
        self.__tests.start()

        return True

    def get_last_coverage_report(self, module_name):
        """
        Return last coverage report

        Args:
            module_name (string): module name
        """
        if self.__tests_running:
            raise CommandError(u'Tests are running. Please wait end of it')

        cmd = self.CLI_TESTS_COV_CMD % (self.CLI, module_name)
        self.logger.debug(u'Test cov cmd: %s' % cmd)
        self.__tests = EndlessConsole(cmd, self.__tests_callback, self.__tests_end_callback)
        self.__tests_running = True
        self.__tests.start()

        return True

    def __docs_callback(self, stdout, stderr):
        """
        Docs cli outputs

        Args:
            stdout (string): stdout message
            stderr (string): stderr message
        """
        message = (stdout if stdout is not None else '') + (stderr if stderr is not None else '')
        self.logger.info(u'Receive docs cmd message: "%s"' % message)
        self.docs_output_event.send(params={u'message': message}, render=False)

    def __docs_end_callback(self, return_code, killed):
        """
        Docs cli ended

        Args:
            return_code (int): command return code
            killed (bool): True if command killed
        """
        self.logger.info(u'Docs command terminated with return code "%s" (killed=%s)' % (return_code, killed))
        self.__docs_running = False

    def generate_documentation(self, module_name):
        """
        Generate documentation

        Args:
            module_name (string): module name
        """
        if self.__docs_running:
            raise CommandError(u'Doc generation is running. Please wait end of it')

        cmd = self.CLI_DOCS_CMD % (self.CLI, module_name)
        self.logger.debug(u'Doc generation cmd: %s' % cmd)
        self.__docs = EndlessConsole(cmd, self.__docs_callback, self.__docs_end_callback)
        self.__docs_running = True
        self.__docs.start()

        return True

    def download_documentation(self, module_name):
        """
        Download documentation (html as archive tar.gz)

        Args:
            module_name (string): module name

        Returns:
            dict: archive infos::

                {
                    data: filepath
                    filename: new filename
                }

        """
        self.logger.debug(u'Download documentation')
        if self.__module_name is None or self.__module_archive is None or self.__module_version is None:
            raise CommandError(u'No module package generated')

        return {
            u'filepath': self.__module_archive,
            u'filename': u'cleepmod_%s_%s.zip' % (module_name, self.__module_version)
        }


