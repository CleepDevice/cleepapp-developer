#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import inspect
import importlib
import re
import json
import copy
from zipfile import ZipFile, ZIP_DEFLATED
from tempfile import NamedTemporaryFile
from cleep.core import CleepModule
from cleep.libs.internals.console import Console, EndlessConsole
from cleep.exception import CommandError, MissingParameter, InvalidParameter
from cleep.common import CATEGORIES
from cleep.libs.internals.installmodule import FRONTEND_DIR, BACKEND_DIR, SCRIPTS_DIR, PATH_FRONTEND, PATH_SCRIPTS, TESTS_DIR
from cleep.libs.internals import __all__ as internals_libs
from cleep.libs.drivers import __all__ as drivers_libs
from cleep.libs.configs import __all__ as configs_libs
from cleep.libs.commands import __all__ as commands_libs
import cleep.libs.internals.tools as Tools


__all__ = ['Developer']


class Developer(CleepModule):
    """
    Developer module: this module is dedicated only for developers.
    It allows implements and configures remotedev in cleep

    Note:
        https://github.com/tangb/cleep-cli
    """
    MODULE_AUTHOR = 'Cleep'
    MODULE_VERSION = '2.2.0'
    MODULE_PRICE = 0
    MODULE_DEPS = []
    MODULE_DESCRIPTION = 'Helps you to develop Cleep applications.'
    MODULE_LONGDESCRIPTION = 'Developer module helps you to develop on Cleep installing \
        and preconfiguring sync tools. It also provides a full page that helps you to \
        check and build your own application.<br/>This module will provide the official way to \
        publish your module on Cleep market.<br/><br/>Lot of resources are available \
        on developer module wiki, have a look and start enjoying Cleep!'
    MODULE_TAGS = ['developer', 'python', 'cleepos', 'module', 'angularjs', 'cleep', 'cli', 'test', 'documentation']
    MODULE_CATEGORY = 'APPLICATION'
    MODULE_COUNTRY = None
    MODULE_URLINFO = 'https://github.com/tangb/cleepmod-developer'
    MODULE_URLHELP = 'https://github.com/tangb/cleepmod-developer/wiki'
    MODULE_URLSITE = None
    MODULE_URLBUGS = 'https://github.com/tangb/cleepmod-developer/issues'

    MODULE_CONFIG_FILE = 'developer.conf'
    DEFAULT_CONFIG = {
        'moduleindev': None
    }

    BUFFER_SIZE = 10

    PATH_MODULE_TESTS = '/root/cleep/modules/%(MODULE_NAME)s/tests/'
    PATH_MODULE_FRONTEND = '/root/cleep/modules/%(MODULE_NAME)s/frontend/'

    CLI = '/usr/local/bin/cleep-cli'
    CLI_WATCHER_CMD = '%s watch --loglevel=40' % CLI
    CLI_TESTS_CMD = '%s modtests --module "%s" --coverage'
    CLI_TESTS_COV_CMD = '%s modtestscov --module "%s" --missing'
    CLI_NEW_APPLICATION_CMD = '%s modcreate --module "%s"'
    CLI_DOCS_CMD = '%s moddocs --module "%s" --preview'
    CLI_DOCS_ZIP_PATH_CMD = '%s moddocspath --module "%s"'

    FRONT_FILE_TYPE_DROP = 'Do not include file'
    FRONT_FILE_TYPE_SERVICE_JS = 'service-js'
    FRONT_FILE_TYPE_COMPONENT_JS = 'component-js'
    FRONT_FILE_TYPE_COMPONENT_HTML = 'component-html'
    FRONT_FILE_TYPE_COMPONENT_CSS = 'component-css'
    FRONT_FILE_TYPE_CONFIG_JS = 'config-js'
    FRONT_FILE_TYPE_CONFIG_HTML = 'config-html'
    FRONT_FILE_TYPE_CONFIG_CSS = 'config-css'
    FRONT_FILE_TYPE_PAGES_JS = 'pages-js'
    FRONT_FILE_TYPE_PAGES_HTML = 'pages-html'
    FRONT_FILE_TYPE_PAGES_CSS = 'pages-css'
    FRONT_FILE_TYPE_RESOURCE = 'resource'
    FRONT_FILE_TYPES = [
        FRONT_FILE_TYPE_DROP,
        FRONT_FILE_TYPE_SERVICE_JS,
        FRONT_FILE_TYPE_COMPONENT_JS,
        FRONT_FILE_TYPE_COMPONENT_HTML,
        FRONT_FILE_TYPE_COMPONENT_CSS,
        FRONT_FILE_TYPE_CONFIG_JS,
        FRONT_FILE_TYPE_CONFIG_HTML,
        FRONT_FILE_TYPE_CONFIG_CSS,
        FRONT_FILE_TYPE_PAGES_JS,
        FRONT_FILE_TYPE_PAGES_HTML,
        FRONT_FILE_TYPE_PAGES_CSS,
        FRONT_FILE_TYPE_RESOURCE
    ]

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled (bool): flag to set debug level to logger
        """
        #init
        CleepModule.__init__(self, bootstrap, debug_enabled)

        #members
        self.__developer_uuid = None
        self.cleep_path = os.path.dirname(inspect.getfile(CleepModule))
        self.__module_name = None
        self.__module_archive = None
        self.__module_version = None
        self.__watcher_task = None
        self.__tests_task = None
        self.__tests_buffer = []
        self.__docs_task = None
        self.__docs_buffer = []

        #events
        self.frontend_restart_event = self._get_event('developer.frontend.restart')
        self.tests_output_event = self._get_event('developer.tests.output')
        self.docs_output_event = self._get_event('developer.docs.output')

    def _configure(self):
        """
        Configure module
        """
        #disable rw if in development
        module_in_dev = self._get_config_field('moduleindev')
        self.logger.debug('Module in development: %s' % module_in_dev)
        if module_in_dev:
            self.logger.info('Module "%s" is in development, disable RO feature' % module_in_dev)
            self.cleep_filesystem.enable_write(root=True, boot=True)

        #add dummy device
        self.logger.debug('device_count=%d' % self._get_device_count())
        if self._get_device_count() == 0:
            self.logger.debug('Add default devices')
            developer = {
                'type': 'developer',
                'name': 'Developer'
            }
            self._add_device(developer)

        #store device uuids for events
        devices = self.get_module_devices()
        self.logger.debug('devices: %s' % devices)
        for uuid in devices:
            if devices[uuid]['type'] == 'developer':
                self.__developer_uuid = uuid

    def _on_start(self):
        """
        Module starts
        """
        #start watcher task
        self.__launch_watcher()

    def _on_stop(self):
        """
        Custom stop: stop remotedev thread
        """
        if self.__watcher_task:
            self.__watcher_task.stop()
        if self.__tests_task:
            self.__tests_task.stop()
        if self.__docs_task:
            self.__docs_task.stop()

    def __launch_watcher(self):
        """
        Launch cleep-cli watch command
        """
        #kill all previous existing cleep-cli instances
        console = Console()
        console.command('/usr/bin/pkill -9 -f cleep-cli')

        self.logger.info('Launch watcher task')
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
        self.__developer_uuid = list(devices.keys())[0]
        devices[self.__developer_uuid].update(data)

        return devices

    def set_module_in_development(self, module_name):
        """
        Set module in development. It save in config the module, and enable debug.
        It also disable debug on old module in debug if any.

        Args:
            module_name (string): module to enable development on
        """
        #disable debug on old module
        old_module = self._get_config_field('moduleindev')
        if old_module:
            try:
                #module may not exist
                if old_module == 'developer':
                    self.set_debug(False)
                elif len(old_module) > 0:
                    self.send_command('set_module_debug', 'system', {'module': old_module, 'debug': False})
            except Exception:
                pass

        #save new module in dev
        self._set_config_field('moduleindev', module_name)
        if module_name == 'developer':
            self.set_debug(True)
        elif len(module_name) > 0:
            self.send_command('set_module_debug', 'system', {'module': module_name, 'debug': True})

        #disable RO feature
        if len(module_name) > 0:
            self.logger.info('Module "%s" is in development, disable RO feature' % module_name)
            self.cleep_filesystem.enable_write(root=True, boot=True)
        else:
            self.logger.info('No module in development, enable RO feature')
            self.cleep_filesystem.disable_write(root=True, boot=True)

    def restart_frontend(self):
        """
        Send event to restart frontend
        """
        self.logger.info('Sending restart event to frontend')
        self.frontend_restart_event.send(to='rpc')

    def create_application(self, module_name):
        """
        Create new application skel

        Args:
            module_name (string): module name
        """
        cmd = self.CLI_NEW_APPLICATION_CMD % (self.CLI, module_name)
        self.logger.debug('Create app cmd: %s' % cmd)

        console = Console()
        res = console.command(cmd, 10.0)
        self.logger.info('Create app cmd result: %s %s' % (res['stdout'], res['stderr']))
        if res['error'] or res['killed'] or res['returncode'] != 0:
            raise CommandError('Error during application creation. Consult the logs.')

        return True

    def __analyze_module_python(self, module_name):
        """
        Analyze package python part

        Args:
            module_name (string): module name

        Returns:
            dict: python package data::

                {
                    metadata (dict): module metadata,
                    files (list): list of python files (libs, module...)
                }

        """
        #init
        errors = []
        warnings = []
        self.logger.debug('Cleep_path=%s' % self.cleep_path)
        modules_path = os.path.join(self.cleep_path, 'modules')

        #get module instance
        try:
            module_ = importlib.import_module('cleep.modules.%s.%s' % (module_name, module_name))
            class_ = getattr(module_, module_name.capitalize())
        except:
            self.logger.exception('Unable to load module "%s". Please check your code' % module_name)
            raise InvalidParameter('Unable to load module "%s". Please check your code' % module_name)

        #check module metadata
        #MODULE_DESCRIPTION
        if not hasattr(class_, 'MODULE_DESCRIPTION'):
            errors.append('Mandatory field MODULE_DESCRIPTION is missing')
        elif not isinstance(getattr(class_, 'MODULE_DESCRIPTION'), str):
            errors.append('Field MODULE_DESCRIPTION must be a string')
        elif len(getattr(class_, 'MODULE_DESCRIPTION')) == 0:
            errors.append('Field MODULE_DESCRIPTION must be provided')
        #MODULE_LONGDESCRIPTION
        if not hasattr(class_, 'MODULE_LONGDESCRIPTION'):
            errors.append('Mandatory field MODULE_LONGDESCRIPTION is missing')
        elif not isinstance(getattr(class_, 'MODULE_LONGDESCRIPTION'), str):
            errors.append('Field MODULE_LONGDESCRIPTION must be a string')
        elif len(getattr(class_, 'MODULE_LONGDESCRIPTION')) == 0:
            errors.append('Field MODULE_LONGDESCRIPTION must be provided')
        #MODULE_CATEGORY
        if not hasattr(class_, 'MODULE_CATEGORY'):
            errors.append('Mandatory field MODULE_CATEGORY is missing')
        elif not isinstance(getattr(class_, 'MODULE_CATEGORY'), str):
            errors.append('Field MODULE_CATEGORY must be a string')
        elif len(getattr(class_, 'MODULE_CATEGORY')) == 0:
            errors.append('Field MODULE_CATEGORY must be provided')
        elif getattr(class_, 'MODULE_CATEGORY') not in CATEGORIES.ALL:
            errors.append('Field MODULE_CATEGORY must be one of possible values (see doc)')
        #MODULE_DEPS
        if not hasattr(class_, 'MODULE_DEPS'):
            errors.append('Mandatory field MODULE_DEPS is missing')
        elif hasattr(class_, 'MODULE_DEPS') and not isinstance(getattr(class_, 'MODULE_DEPS'), list):
            errors.append('Field MODULE_DEPS must be a list')
        #MODULE_VERSION
        version_pattern = re.compile(r'\d+\.\d+\.\d+')
        if not hasattr(class_, 'MODULE_VERSION'):
            errors.append('Mandatory field MODULE_VERSION is missing')
        elif not isinstance(getattr(class_, 'MODULE_VERSION'), str):
            errors.append('Field MODULE_VERSION must be a string')
        elif len(getattr(class_, 'MODULE_VERSION')) == 0:
            errors.append('Field MODULE_VERSION must be provided')
        elif version_pattern.match(getattr(class_, 'MODULE_VERSION')) is None:
            errors.append('Field MODULE_VERSION must match this format <number>.<number>.<number>')
        #MODULE_TAGS
        if not hasattr(class_, 'MODULE_TAGS'):
            errors.append('Mandatory field MODULE_TAGS is missing')
        elif not isinstance(getattr(class_, 'MODULE_TAGS'), list):
            errors.append('Field MODULE_TAGS must be a list')
        elif len(getattr(class_, 'MODULE_TAGS')) == 0:
            warnings.append('Field MODULE_TAGS should contains strings to help finding your module')
        #MODULE_URLINFO
        if not hasattr(class_, 'MODULE_URLINFO'):
            errors.append('Mandatory field MODULE_URLINFO is missing')
        elif not isinstance(getattr(class_, 'MODULE_URLINFO'), str) and getattr(class_, 'MODULE_URLINFO') is not None:
            errors.append('Field MODULE_URLINFO must be a string or None')
        elif getattr(class_, 'MODULE_URLINFO') is None or len(getattr(class_, 'MODULE_URLINFO')) == 0:
            warnings.append('Field MODULE_URLINFO should be filled with url that describes your module')
        #MODULE_URLHELP
        if not hasattr(class_, 'MODULE_URLHELP'):
            errors.append('Mandatory field MODULE_URLHELP is missing')
        elif not isinstance(getattr(class_, 'MODULE_URLHELP'), str) and getattr(class_, 'MODULE_URLHELP') is not None:
            errors.append('Field MODULE_URLHELP must be a string or None')
        elif getattr(class_, 'MODULE_URLHELP') is None or len(getattr(class_, 'MODULE_URLHELP')) == 0:
            warnings.append('Field MODULE_URLHELP should be filled with url that gives access to your module support page')
        #MODULE_URLSITE
        if not hasattr(class_, 'MODULE_URLSITE'):
            errors.append('Mandatory field MODULE_URLSITE is missing')
        elif not isinstance(getattr(class_, 'MODULE_URLSITE'), str) and getattr(class_, 'MODULE_URLSITE') is not None:
            errors.append('Field MODULE_URLSITE must be a string or None')
        elif getattr(class_, 'MODULE_URLSITE') is None or len(getattr(class_, 'MODULE_URLSITE')) == 0:
            warnings.append('Field MODULE_URLSITE should be filled with module website url')
        #MODULE_URLBUGS
        if not hasattr(class_, 'MODULE_URLBUGS'):
            errors.append('Mandatory field MODULE_URLBUGS is missing')
        elif not isinstance(getattr(class_, 'MODULE_URLBUGS'), str) and getattr(class_, 'MODULE_URLBUGS') is not None:
            errors.append('Field MODULE_URLBUGS must be a string or None')
        elif getattr(class_, 'MODULE_URLBUGS') is None or len(getattr(class_, 'MODULE_URLBUGS')) == 0:
            warnings.append('Field MODULE_URLBUGS should be filled with module bugs tracking system url')
        #MODULE_COUNTRY
        if not hasattr(class_, 'MODULE_COUNTRY'):
            errors.append('Mandatory field MODULE_COUNTRY is missing')
        elif not isinstance(getattr(class_, 'MODULE_COUNTRY'), str) and getattr(class_, 'MODULE_COUNTRY') is not None:
            errors.append('Field MODULE_COUNTRY must be a string or None')

        #build package metadata
        label = getattr(class_, 'MODULE_LABEL', module_name.capitalize())
        description = getattr(class_, 'MODULE_DESCRIPTION', '')
        longdescription = getattr(class_, 'MODULE_LONGDESCRIPTION', '')
        category = getattr(class_, 'MODULE_CATEGORY', '')
        deps = getattr(class_, 'MODULE_DEPS', [])
        version = getattr(class_, 'MODULE_VERSION', '')
        tags = getattr(class_, 'MODULE_TAGS', [])
        urls = {
            'info': None,
            'help': None,
            'bugs': None,
            'site': None
        }
        urls['info'] = getattr(class_, 'MODULE_URLINFO', '')
        urls['help'] = getattr(class_, 'MODULE_URLHELP', '')
        urls['site'] = getattr(class_, 'MODULE_URLSITE', '')
        urls['bugs'] = getattr(class_, 'MODULE_URLBUGS', '')
        country = getattr(class_, 'MODULE_COUNTRY', '')
        price = getattr(class_, 'MODULE_PRICE', 0)
        author = getattr(class_, 'MODULE_AUTHOR', '')
        metadata = {
            'label': label,
            'description': description,
            'longdescription': longdescription,
            'category': category,
            'deps': deps,
            'version': version,
            'tags': tags,
            'country': country,
            'urls': urls,
            'price': price,
            'author': author
        }
        self.logger.debug('Module "%s" metadata: %s' % (module_name, metadata))

        #add main module file
        files = {
            'module': None,
            'libs': []
        }
        module_main_fullpath = inspect.getfile(module_).replace('.pyc', '.py')
        (module_path, module_main_filename) = os.path.split(module_main_fullpath)
        files['module'] = {
            'fullpath': module_main_fullpath,
            'path': module_main_fullpath.replace(modules_path, '')[1:],
            'filename': module_main_filename
        }
        self.logger.debug('Main module file: %s' % module_main_fullpath)

        #get all files to package
        paths = []
        for root, _, filenames in os.walk(module_path):
            for filename in filenames:
                fullpath = os.path.join(root, filename)
                (file_no_ext, ext) = os.path.splitext(filename)
                if not file_no_ext.lower().endswith('formatter') and not file_no_ext.lower().endswith('event') \
                    and filename not in (module_main_filename) and ext == '.py':
                    self.logger.debug('File to import: %s' % fullpath)
                    paths.append(os.path.split(fullpath)[0])
                    files['libs'].append({
                        'fullpath': fullpath,
                        'path': fullpath.replace(modules_path, '')[1:],
                        'filename': os.path.basename(fullpath),
                        'selected': True
                    })

        #check missing __init__.py
        init_py_path = os.path.join(module_path, '__init__.py')
        if not os.path.exists(init_py_path):
            errors.append('Mandatory file "%s" is missing. Please add empty file. More infos <a href="https://docs.python.org/2.7/tutorial/modules.html#packages" target="_blank">here</a>.' % init_py_path)
        for path in paths:
            init_py_path = os.path.join(path, '__init__.py')
            if not os.path.exists(init_py_path):
                errors.append('Mandatory file "%s" is missing. Please add empty file. More infos <a href="https://docs.python.org/2.7/tutorial/modules.html#packages" target="_blank">here</a>.' % init_py_path)

        #get events
        events = []
        for afile in os.listdir(module_path):
            fullpath = os.path.join(module_path, afile)
            (event, ext) = os.path.splitext(afile)
            parts = Tools.full_split_path(fullpath)
            if event.lower().find('event') >= 0 and ext == '.py':
                self.logger.debug('Loading event "%s"' % 'cleep.modules.%s.%s' % (parts[-2], event))
                try:
                    mod_ = importlib.import_module('cleep.modules.%s.%s' % (parts[-2], event))
                    event_class_name = next((item for item in dir(mod_) if item.lower() == event.lower()), None)
                    if event_class_name:
                        class_ = getattr(mod_, event_class_name)
                        events.append({
                            'fullpath': fullpath,
                            'path': '%s.py' % os.path.join(parts[-2], event),
                            'filename': os.path.basename(fullpath),
                            'name': event_class_name,
                            'selected': True
                        })
                    else:
                        self.logger.debug('Event class must have the same name than filename (%s)' % afile)
                        errors.append('Event class must have the same name than filename (%s)' % afile)
                except Exception:
                    self.logger.exception('Unable to load event %s' % afile)
                    errors.append('Unable to load event %s' % afile)

        #get formatters
        formatters = []
        for afile in os.listdir(module_path):
            fullpath = os.path.join(module_path, afile)
            (formatter, ext) = os.path.splitext(afile)
            parts = Tools.full_split_path(fullpath)
            if formatter.lower().find('formatter') >= 0 and ext == '.py':
                self.logger.debug('Loading formatter "%s"' % 'cleep.modules.%s.%s' % (parts[-2], formatter))
                try:
                    mod_ = importlib.import_module('cleep.modules.%s.%s' % (parts[-2], formatter))
                    formatter_class_name = next((item for item in dir(mod_) if item.lower() == formatter.lower()), None)
                    if formatter_class_name:
                        class_ = getattr(mod_, formatter_class_name)
                        formatters.append({
                            'fullpath': fullpath,
                            'path': '%s.py' % os.path.join(parts[-2], formatter),
                            'filename': os.path.basename(fullpath),
                            'name': formatter_class_name,
                            'selected': True
                        })
                    else:
                        self.logger.debug('Formatter class must have the same name than filename (%s)' % afile)
                        errors.append('Formatter class must have the same name than filename (%s)' % afile)
                except Exception:
                    self.logger.exception('Unable to load formatter %s' % afile)
                    errors.append('Unable to load formatter %s' % afile)

        return {
            'data': {
                'files': files,
                'events': sorted(events, key=lambda k: k['fullpath']),
                'formatters': sorted(formatters, key=lambda k: k['fullpath']),
                'errors': errors,
                'warnings': warnings
            },
            'metadata': metadata,
        }

    def __fill_js_file_types(self, files, desc_json):
        """
        Fill file types as well as possible
        """
        #use desc.json content if possible
        if desc_json:
            #set global
            if 'global' in desc_json and 'js' in desc_json['global']:
                #set service and component-js
                for key in desc_json['global']['js']:
                    if key not in files:
                        continue
                    if key.find('.service.js') >= 0:
                        files[key]['type'] = self.FRONT_FILE_TYPE_SERVICE_JS
                    else:
                        files[key]['type'] = self.FRONT_FILE_TYPE_COMPONENT_JS

                #set component-html
                if 'html' in desc_json['global']:
                    for key in desc_json['global']['html']:
                        if key in files:
                            files[key]['type'] = self.FRONT_FILE_TYPE_COMPONENT_HTML

                #set component-css
                if 'css' in desc_json['global']:
                    for key in desc_json['global']['css']:
                        if key in files:
                            files[key]['type'] = self.FRONT_FILE_TYPE_COMPONENT_CSS

            #set config
            if 'config' in desc_json:
                #config-js
                if 'js' in desc_json['config']:
                    for key in desc_json['config']['js']:
                        if key in files:
                            files[key]['type'] = self.FRONT_FILE_TYPE_CONFIG_JS

                #config-html
                if 'html' in desc_json['config']:
                    for key in desc_json['config']['html']:
                        if key in files:
                            files[key]['type'] = self.FRONT_FILE_TYPE_CONFIG_HTML

                #config-css
                if 'css' in desc_json['config']:
                    for key in desc_json['config']['css']:
                        if key in files:
                            files[key]['type'] = self.FRONT_FILE_TYPE_CONFIG_CSS

            #set pages
            if 'pages' in desc_json and len(desc_json['pages']) > 0:
                for page in desc_json['pages']:
                    #pages-js
                    if 'js' in desc_json['pages'][page]:
                        for key in desc_json['pages'][page]['js']:
                            if key in files:
                                files[key]['type'] = self.FRONT_FILE_TYPE_PAGES_JS

                    #pages-html
                    if 'html' in desc_json['pages'][page]:
                        for key in desc_json['pages'][page]['html']:
                            if key in files:
                                files[key]['type'] = self.FRONT_FILE_TYPE_PAGES_HTML

                    #pages-css
                    if 'css' in desc_json['pages'][page]:
                        for key in desc_json['pages'][page]['css']:
                            if key in files:
                                files[key]['type'] = self.FRONT_FILE_TYPE_PAGES_CSS

            #set resources
            if 'res' in desc_json:
                for key in desc_json['res']:
                    if key in files:
                        files[key]['type'] = self.FRONT_FILE_TYPE_RESOURCE

        else:
            #no desc.json file, try to guess empty types
            for key in files:
                if key == 'icon':
                    #icon field, drop
                    continue
                if files[key]['type'] != self.FRONT_FILE_TYPE_DROP:
                    #drop already found type
                    continue

                #try to identify file type
                if key.find('.service.js') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_SERVICE_JS
                elif key.find('.config.js') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_CONFIG_JS
                elif key.find('.config.html') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_CONFIG_HTML
                elif key.find('.config.css') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_CONFIG_CSS
                elif key.find('.widget.js') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_COMPONENT_JS
                elif key.find('.widget.html') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_COMPONENT_HTML
                elif key.find('.widget.css') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_COMPONENT_CSS
                elif key.find('.page.js') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_PAGES_JS
                elif key.find('.page.html') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_PAGES_HTML
                elif key.find('.page.css') > 0:
                    files[key]['type'] = self.FRONT_FILE_TYPE_PAGES_CSS
                elif files[key]['ext'] in ('png', 'jpg', 'jpeg', 'gif', 'eot', 'woff', 'woff2', 'svg', 'ttf'):
                    files[key]['type'] = self.FRONT_FILE_TYPE_RESOURCE
                elif key == 'desc.json':
                    files[key]['type'] = self.FRONT_FILE_TYPE_RESOURCE

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
            ext = js_files[js_file]['ext'].lower()
            if ext in ('jpg', 'jpeg', 'png', 'gif'):
                images.append(js_files[js_file])
            if ext == 'html':
                htmls.append(js_files[js_file])

        #no image, no need to go further
        if len(images) == 0:
            return warnings

        #cache html files content
        for html in htmls:
            fdesc = self.cleep_filesystem.open(html['fullpath'], 'r')
            cacheds.append('\n'.join(fdesc.readlines()))
            self.cleep_filesystem.close(fdesc)

        #check directive usage for found images
        for image in images:
            pattern = r"mod-img-src\s*=\s*[\"']\s*%s\s*[\"']" % image['path']
            self.logger.debug('Mod-img-src pattern: %s' % pattern)
            found = False
            for cached in cacheds:
                matches = re.finditer(pattern, cached, re.MULTILINE)
                if len(list(matches)) > 0:
                    found = True
            if not found:
                warnings.append('Image "%s" may not be displayed properly because mod-img-src directive wasn\'t used' % image['filename'])

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
        module_path = os.path.join(PATH_FRONTEND, 'js/modules/', module_name)
        self.logger.debug('module_path=%s' % module_path)
        if not os.path.exists(module_path):
            raise CommandError('Module "%s" has no javascript' % module_name)
        for root, _, filenames in os.walk(module_path):
            for afile in filenames:
                self.logger.debug('root=%s f=%s' % (root, afile))
                #drop some files
                if afile.startswith('.') or afile.startswith('~') or afile.endswith('.tmp'):
                    continue

                #get file values
                fullpath = os.path.join(root, afile)
                filepath = os.path.join(root.replace(module_path, ''), afile)
                if filepath[0] == os.path.sep:
                    filepath = filepath[1:]
                filename = afile

                #mandatory field
                mandatory = False
                type_ = self.FRONT_FILE_TYPE_DROP
                if filename == 'desc.json':
                    mandatory = True
                    type_ = self.FRONT_FILE_TYPE_RESOURCE

                #append file infos
                all_files[filepath] = {
                    'fullpath': fullpath,
                    'path': filepath,
                    'filename': filename,
                    'ext': os.path.splitext(fullpath)[1].replace('.', ''),
                    'mandatory': mandatory,
                    'type': type_
                }
        self.logger.debug('all_files: %s' % all_files)

        #load existing description file
        desc_json = ''
        desc_json_path = os.path.join(PATH_FRONTEND, 'js/modules/', module_name, 'desc.json')
        self.logger.debug('desc.json path: %s' % desc_json_path)
        if os.path.exists(desc_json_path):
            desc_json = self.cleep_filesystem.read_json(desc_json_path)

        #fill file types if possible
        all_files = self.__fill_js_file_types(all_files, desc_json)

        #fill changelog
        changelog = ''
        if desc_json and 'changelog' in desc_json:
            changelog = desc_json['changelog']

        #set icon
        icon = 'bookmark'
        if desc_json and 'icon' in desc_json:
            icon = desc_json['icon']

        #check usage of mod-img-src directive in front source code
        warnings = self.__check_mdimgsrc_directive(all_files)

        return {
            'data': {
                'files': sorted(all_files.values(), key=lambda k: k['fullpath']),
                'filetypes': self.FRONT_FILE_TYPES,
                'errors': errors,
                'warnings': warnings
            },
            'icon': icon,
            'changelog': changelog
        }

    def __analyze_scripts(self, module_name):
        """
        Analyze scripts for specified module

        Args:
            module_name (string): module name to search scripts for

        Returns:
            dict: scripts infos::

                {
                    preinst: {
                        found (bool): pre-install script found or not
                        fullpath (string): script fullpath
                    },
                    postinst: {
                        found (bool): pre-install script found or not
                        fullpath (string): script fullpath
                    },
                    preuninst: {
                        found (bool): pre-install script found or not
                        fullpath (string): script fullpath
                    },
                    postuninst: {
                        found (bool): pre-install script found or not
                        fullpath (string): script fullpath
                    }
                }

        """
        script_preinst = os.path.join(PATH_SCRIPTS, module_name, 'preinst.sh')
        script_postinst = os.path.join(PATH_SCRIPTS, module_name, 'postinst.sh')
        script_preuninst = os.path.join(PATH_SCRIPTS, module_name, 'preuninst.sh')
        script_postuninst = os.path.join(PATH_SCRIPTS, module_name, 'postuninst.sh')

        return {
            'preinst': {
                'found': os.path.exists(script_preinst),
                'fullpath': script_preinst
            },
            'postinst': {
                'found': os.path.exists(script_postinst),
                'fullpath': script_postinst
            },
            'preuninst': {
                'found': os.path.exists(script_preuninst),
                'fullpath': script_preuninst
            },
            'postuninst': {
                'found': os.path.exists(script_postuninst),
                'fullpath': script_postuninst
            }
        }

    def __analyze_tests(self, module_name):
        """
        Analyze tests for specified module

        Args:
            module_name (string): module name to search tests for

        Returns:

        """
        errors = []
        warnings = []

        #iterate over files in supposed tests module directory
        all_files = {}
        tests_path = self.PATH_MODULE_TESTS % {'MODULE_NAME':module_name}
        self.logger.debug('tests_path=%s' % tests_path)
        if not os.path.exists(tests_path):
            raise CommandError('Module "%s" has no tests directory' % module_name)
        for root, _, filenames in os.walk(tests_path):
            for afile in filenames:
                self.logger.debug('root=%s f=%s' % (root, afile))
                #drop some files
                if afile.startswith('.') or afile.startswith('~') or afile.endswith('.tmp') or root.find('__pycache__') >= 0:
                    self.logger.debug('===> drop file')
                    continue

                #get file values
                fullpath = os.path.join(root, afile)
                filepath = os.path.join(root.replace(tests_path, ''), afile)
                if filepath[0] == os.path.sep:
                    filepath = filepath[1:]
                filename = afile

                ext = os.path.splitext(fullpath)[1].replace('.', '')
                self.logger.debug('Extension: %s' % ext)
                #keep only python files
                if ext == 'py':
                    all_files[filepath] = {
                        'fullpath': fullpath,
                        'path': filepath,
                        'filename': filename,
                        'ext': ext
                    }

        #check for errors and warnings
        if '__init__.py' not in all_files:
            errors.append('__init__.py files is mandatory in tests directory. Please add it.')

        return {
            'files': list(all_files.values()),
            'errors': errors,
            'warnings': warnings
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
        if module_name is None or len(module_name) == 0:
            raise MissingParameter('Parameter "module_name" is missing')
        module_path = os.path.join(self.cleep_path, 'modules', module_name, '%s.py' % module_name)
        if not os.path.exists(module_path):
            raise InvalidParameter('Module "%s" does not exist' % module_name)

        #analyze python part
        analyze_python = self.__analyze_module_python(module_name)
        self.logger.debug('analyze_python: %s' % analyze_python)

        #analyze front part
        analyze_js = self.__analyze_module_js(module_name)
        self.logger.debug('analyze_js: %s' % analyze_js)

        #analyze scripts part
        analyze_scripts = self.__analyze_scripts(module_name)
        self.logger.debug('analyze_scripts: %s' % analyze_scripts)

        #analyze tests part
        analyze_tests = self.__analyze_tests(module_name)
        self.logger.debug('analyze_tests: %s' % analyze_tests)

        return {
            'python': analyze_python['data'],
            'js': analyze_js['data'],
            'scripts': analyze_scripts,
            'tests': analyze_tests,
            'changelog': analyze_js['changelog'],
            'icon': analyze_js['icon'],
            'metadata': analyze_python['metadata']
        }

    def generate_desc_json(self, js_files, icon):
        """
        Generate desc.json file inside module directory

        Args:
            js_files (dict): js.files part of data returned by analyze_module command
            icon (string): module icon string

        Returns:
            bool: True if file generated successfully
        """
        content = {
            'icon': icon,
            'global': {
                'js': [],
                'html': [],
                'css': []
            },
            'config': {
                'js': [],
                'html': [],
                'css': []
            },
            'res': []
        }

        #iterates over files
        for afile in js_files:
            if afile['type'] == self.FRONT_FILE_TYPE_SERVICE_JS:
                content['global']['js'].append(afile['path'])
            elif afile['type'] == self.FRONT_FILE_TYPE_COMPONENT_JS:
                content['global']['js'].append(afile['path'])
            elif afile['type'] == self.FRONT_FILE_TYPE_COMPONENT_HTML:
                content['global']['html'].append(afile['path'])
            elif afile['type'] == self.FRONT_FILE_TYPE_COMPONENT_CSS:
                content['global']['css'].append(afile['path'])
            elif afile['type'] == self.FRONT_FILE_TYPE_CONFIG_JS:
                content['config']['js'].append(afile['path'])
            elif afile['type'] == self.FRONT_FILE_TYPE_CONFIG_HTML:
                content['config']['html'].append(afile['path'])
            elif afile['type'] == self.FRONT_FILE_TYPE_CONFIG_CSS:
                content['config']['css'].append(afile['path'])
            elif afile['type'] == self.FRONT_FILE_TYPE_RESOURCE and afile['path'] != 'desc.json':
                content['res'].append(afile['path'])
        self.logger.debug('Generated desc.json content: %s' % content)

        #write json file to js module directory in development env (it will be sync automatically by watcher)
        if len(js_files) > 0:
            module_name = self._get_config_field('moduleindev')
            js_path = os.path.join(self.PATH_MODULE_FRONTEND % {'MODULE_NAME': module_name}, 'desc.json')
            self.logger.debug('js_path=%s' % js_path)
            return self.cleep_filesystem.write_json(js_path, content)

        self.logger.warning('Nothing to write to desc.json file')
        return False

    def build_package(self, module_name, data):
        """
        Build module package archive in zip format.
        Archive is not protected by password

        Args:
            module_name (string): module name
            data (dict): data returned by analyze_module command

        Returns:
            string: url of archive to download or None if error occured
        """
        #init
        self.__module_archive = None
        self.__module_name = None
        self.__module_version = None

        #build module description file (module.json)
        fdesc = NamedTemporaryFile(delete=False, encoding='utf-8', mode='w')
        module_json = fdesc.name
        metadata = copy.deepcopy(data['metadata'])
        metadata['icon'] = data['icon']
        metadata['changelog'] = data['changelog']
        fdesc.write(str(json.dumps(metadata, indent=4, ensure_ascii=False, sort_keys=True)))
        fdesc.close()

        #build zip archive
        fdesc = NamedTemporaryFile(delete=False)
        module_archive = fdesc.name
        self.logger.debug('Archive filepath: %s' % module_archive)
        archive = ZipFile(fdesc, 'w', ZIP_DEFLATED)

        #add js files
        for afile in data['js']['files']:
            if afile['type'] != self.FRONT_FILE_TYPE_DROP:
                archive.write(afile['fullpath'], os.path.join(FRONTEND_DIR, 'js', 'modules', module_name, afile['path']))

        #add python files
        path_in = data['python']['files']['module']['fullpath']
        path_out = os.path.join(BACKEND_DIR, 'modules', data['python']['files']['module']['path'])
        archive.write(path_in, path_out)
        for afile in data['python']['files']['libs']:
            if afile['selected']:
                path_in = afile['fullpath']
                path_out = os.path.join(BACKEND_DIR, 'modules', afile['path'])
                archive.write(path_in, path_out)
        for afile in data['python']['events']:
            if afile['selected']:
                path_in = afile['fullpath']
                path_out = os.path.join(BACKEND_DIR, 'modules', afile['path'])
                archive.write(path_in, path_out)
        for afile in data['python']['formatters']:
            if afile['selected']:
                path_in = afile['fullpath']
                path_out = os.path.join(BACKEND_DIR, 'modules', afile['path'])
                archive.write(path_in, path_out)

        #add tests
        for afile in data['tests']['files']:
            path_in = afile['fullpath']
            path_out = os.path.join(TESTS_DIR, afile['path'])
            archive.write(path_in, path_out)

        #add scripts
        if data['scripts']['preinst']['found']:
            archive.write(data['scripts']['preinst']['fullpath'], os.path.join(SCRIPTS_DIR, 'preinst.sh'))
        if data['scripts']['postinst']['found']:
            archive.write(data['scripts']['postinst']['fullpath'], os.path.join(SCRIPTS_DIR, 'postinst.sh'))
        if data['scripts']['preuninst']['found']:
            archive.write(data['scripts']['preuninst']['fullpath'], os.path.join(SCRIPTS_DIR, 'preuninst.sh'))
        if data['scripts']['postuninst']['found']:
            archive.write(data['scripts']['postuninst']['fullpath'], os.path.join(SCRIPTS_DIR, 'postuninst.sh'))

        #add module.json
        archive.write(module_json, 'module.json')

        #close archive
        archive.close()

        #clean some stuff
        if os.path.exists(module_json):
            os.remove(module_json)

        #save now related package infos to make sure everything is completed successfully
        self.__module_archive = module_archive
        self.__module_name = module_name
        self.__module_version = data['metadata']['version']
        self.logger.info('Package for app "%s" has been built into "%s"' % (self.__module_name, self.__module_archive))

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
        self.logger.debug('Download package')
        if self.__module_name is None or self.__module_archive is None or self.__module_version is None:
            raise CommandError('No module package generated')

        self.logger.debug('Download file path "%s" for module "%s"' % (self.__module_archive, self.__module_name))
        return {
            'filepath': self.__module_archive,
            'filename': 'cleepmod_%s_%s.zip' % (self.__module_name, self.__module_version)
        }

    def __tests_callback(self, stdout, stderr):
        """
        Tests cli outputs

        Args:
            stdout (list): stdout message
            stderr (list): stderr message
        """
        message = (stdout if stdout is not None else '') + (stderr if stderr is not None else '')
        self.logger.debug('Receive tests cmd message: "%s"' % message)
        self.__tests_buffer.append(message)
        #send every 10 lines to prevent bus from dropping messages
        if len(self.__tests_buffer) % self.BUFFER_SIZE == 0:
            self.logger.debug('Send tests output event')
            self.tests_output_event.send(params={'messages': self.__tests_buffer[:self.BUFFER_SIZE]}, to='rpc', render=False)
            del self.__tests_buffer[:self.BUFFER_SIZE]

    def __tests_end_callback(self, return_code, killed):
        """
        Tests cli ended

        Args:
            return_code (int): command return code
            killed (bool): True if command killed
        """
        self.logger.info('Tests command terminated with return code "%s" (killed=%s)' % (return_code, killed))
        self.tests_output_event.send(params={'messages': self.__tests_buffer[:self.BUFFER_SIZE]}, to='rpc', render=False)
        del self.__tests_buffer[:self.BUFFER_SIZE]
        self.__tests_task = None

    def launch_tests(self, module_name):
        """
        Launch unit tests

        Args:
            module_name (string): module name
        """
        if self.__tests_task:
            raise CommandError('Tests are already running')

        cmd = self.CLI_TESTS_CMD % (self.CLI, module_name)
        self.logger.debug('Test cmd: %s' % cmd)
        self.__tests_task = EndlessConsole(cmd, self.__tests_callback, self.__tests_end_callback)
        self.__tests_task.start()

        return True

    def get_last_coverage_report(self, module_name):
        """
        Return last coverage report

        Args:
            module_name (string): module name
        """
        if self.__tests_task:
            raise CommandError('Tests are running. Please wait end of it')

        cmd = self.CLI_TESTS_COV_CMD % (self.CLI, module_name)
        self.logger.debug('Test cov cmd: %s' % cmd)
        self.__tests_task = EndlessConsole(cmd, self.__tests_callback, self.__tests_end_callback)
        self.__tests_task.start()

        return True

    def __docs_callback(self, stdout, stderr):
        """
        Docs cli outputs

        Args:
            stdout (list): stdout message
            stderr (list): stderr message
        """
        message = (stdout if stdout is not None else '') + (stderr if stderr is not None else '')
        self.logger.debug('Receive docs cmd message: "%s"' % message)
        self.__docs_buffer.append(message)
        #send every 10 lines to prevent bus from dropping messages
        if len(self.__docs_buffer) % self.BUFFER_SIZE == 0:
            self.logger.debug('Send docs output event')
            self.docs_output_event.send(params={'messages': self.__docs_buffer[:self.BUFFER_SIZE]}, to='rpc', render=False)
            del self.__docs_buffer[:self.BUFFER_SIZE]

    def __docs_end_callback(self, return_code, killed):
        """
        Docs cli ended

        Args:
            return_code (int): command return code
            killed (bool): True if command killed
        """
        self.logger.info('Docs command terminated with return code "%s" (killed=%s)' % (return_code, killed))
        self.docs_output_event.send(params={'messages': self.__docs_buffer[:self.BUFFER_SIZE]}, to='rpc', render=False)
        del self.__docs_buffer[:self.BUFFER_SIZE]
        self.__docs_task = None

    def generate_documentation(self, module_name):
        """
        Generate documentation

        Args:
            module_name (string): module name
        """
        if self.__docs_task:
            raise CommandError('Doc generation is running. Please wait end of it')

        cmd = self.CLI_DOCS_CMD % (self.CLI, module_name)
        self.logger.debug('Doc generation cmd: %s' % cmd)
        self.__docs_task = EndlessConsole(cmd, self.__docs_callback, self.__docs_end_callback)
        self.__docs_task.start()

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

        Raises:
            CommandError: command failed error

        """
        self.logger.info('Download documentation html archive')

        cmd = self.CLI_DOCS_ZIP_PATH_CMD % (self.CLI, module_name)
        self.logger.debug('Doc zip path cmd: %s' % cmd)
        console = Console()
        res = console.command(cmd)
        if res['returncode'] != 0:
            raise CommandError(''.join(res['stdout']))

        zip_path = res['stdout'][0].split('=')[1]
        self.logger.debug('Module "%s" docs path "%s"' % (module_name, zip_path))
        return {
            'filepath': zip_path,
            'filename': os.path.basename(zip_path)
        }


