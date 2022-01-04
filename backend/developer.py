#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import inspect
import json
from cleep.core import CleepModule
from cleep.libs.internals.console import Console, EndlessConsole
from cleep.exception import CommandError, MissingParameter, InvalidParameter
from cleep.libs.internals import __all__ as internals_libs
from cleep.libs.drivers import __all__ as drivers_libs
from cleep.libs.configs import __all__ as configs_libs
from cleep.libs.commands import __all__ as commands_libs


__all__ = ['Developer']


class Developer(CleepModule):
    """
    Developer module: this module is only useful for developers.
    It installs remote Cleep development environment. You can find more information directly on cleepapp-developer github page

    Note:
        https://github.com/tangb/cleepapp-developer/wiki
    """
    MODULE_AUTHOR = 'Cleep'
    MODULE_VERSION = '3.0.0'
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
    CLI_SYNC_MODULE_CMD = CLI + ' modsync --module=%s'
    CLI_TESTS_CMD = '%s modtests --module "%s" --coverage'
    CLI_TESTS_COV_CMD = '%s modtestscov --module "%s" --missing'
    CLI_NEW_APPLICATION_CMD = '%s modcreate --module "%s"'
    CLI_DOCS_CMD = '%s moddocs --module "%s" --preview'
    CLI_DOCS_ZIP_PATH_CMD = '%s moddocspath --module "%s"'
    CLI_CHECK_BACKEND_CMD = '%s modcheckbackend --module "%s" --json'
    CLI_CHECK_FRONTEND_CMD = '%s modcheckfrontend --module "%s" --json'
    CLI_CHECK_SCRIPTS_CMD = '%s modcheckscripts --module "%s" --json'
    CLI_CHECK_TESTS_CMD = '%s modchecktests --module "%s" --json'
    CLI_CHECK_CODE_CMD = '%s modcheckcode --module "%s" --threshold 7 --json'
    CLI_CHECK_CHANGELOG_CMD = '%s modcheckchangelog --module "%s" --json'
    CLI_BUILD_APP_CMD = '%s modbuild --module "%s"'

    def __init__(self, bootstrap, debug_enabled):
        """
        Constructor

        Args:
            bootstrap (dict): bootstrap objects
            debug_enabled (bool): flag to set debug level to logger
        """
        CleepModule.__init__(self, bootstrap, debug_enabled)

        # members
        self.__developer_uuid = None
        self.cleep_path = os.path.dirname(inspect.getfile(CleepModule))
        self.__last_application_build = None
        self.__watcher_task = None
        self.__tests_task = None
        self.__tests_buffer = []
        self.__docs_task = None
        self.__docs_buffer = []

        # events
        self.tests_output_event = self._get_event('developer.tests.output')
        self.docs_output_event = self._get_event('developer.docs.output')
        self.frontend_restart_event = self._get_event('developer.frontend.restart')

    def _configure(self):
        """
        Configure module
        """
        # disable rw if in development
        module_in_dev = self._get_config_field('moduleindev')
        self.logger.debug('Module in development: %s' % module_in_dev)
        if module_in_dev:
            self.logger.info('Module "%s" is in development, disable RO feature' % module_in_dev)
            self.cleep_filesystem.enable_write(root=True, boot=True)

        # add dummy device
        self.logger.debug('device_count=%d' % self._get_device_count())
        if self._get_device_count() == 0:
            self.logger.debug('Add default devices')
            developer = {
                'type': 'developer',
                'name': 'Developer'
            }
            self._add_device(developer)

        # store device uuids for events
        devices = self.get_module_devices()
        self.logger.debug('devices: %s' % devices)
        for uuid in devices:
            if devices[uuid]['type'] == 'developer':
                self.__developer_uuid = uuid

    def _on_start(self):
        """
        Module starts
        """
        self.__start_watcher()

    def _on_stop(self):
        """
        Custom stop: stop remotedev thread
        """
        self.__stop_watcher()
        if self.__tests_task:
            self.__tests_task.stop()
        if self.__docs_task:
            self.__docs_task.stop()

    def __start_watcher(self):
        """
        Launch cleep-cli watch command
        """
        self.__kill_watchers()

        self.logger.info('Launch watcher task')
        self.__watcher_task = EndlessConsole(self.CLI_WATCHER_CMD, self.__watcher_callback, self.__watcher_end_callback)
        self.__watcher_task.start()

    def __stop_watcher(self):
        """
        Stop running watcher instance
        """
        if self.__watcher_task:
            self.__watcher_task.stop()
        self.__kill_watchers()

    def __kill_watchers(self):
        """
        Kill all watchers instances
        """
        console = Console()
        console.command('/usr/bin/pkill -9 -f "cleep-cli watch"')

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
        if self.__tests_task:
            self.tests_output_event.send(params={'messages': '====== Tests crashes. Run tests manually please to check errors ====='}, to='rpc', render=False)

        self.__start_watcher()

    def get_module_devices(self):
        """
        Return module devices
        """
        devices = super().get_module_devices()
        data = {}
        self.__developer_uuid = list(devices.keys())[0]
        devices[self.__developer_uuid].update(data)

        return devices

    def restart_frontend(self):
        """
        Send event to restart frontend
        """
        self.logger.info('Sending restart event to frontend')
        self.frontend_restart_event.send(to='rpc')

    def select_application_for_development(self, module_name):
        """
        Select application for development. It save in config the module, and enable debug.
        It also disables debug on previous module in debug if any.

        Args:
            module_name (string): module to enable development on, None to disable development mode
        """
        self.__last_application_build = None

        # disable debug on old module
        old_module = self._get_config_field('moduleindev')
        if old_module:
            self.__set_module_debug(old_module, False)

        # save new module in dev
        self._set_config_field('moduleindev', module_name)

        # enable or disable dev mode
        if module_name:
            self.__set_module_debug(module_name, True)
            self.logger.info('Application "%s" is in development, disable RO feature' % module_name)
            self.cleep_filesystem.enable_write(root=True, boot=True)
        else:
            self.logger.info('No application in development, enable RO feature')
            self.cleep_filesystem.disable_write(root=True, boot=True)

    def __set_module_debug(self, module_name, debug):
        """
        Enable or disable debug on specified module

        Args:
            module_name (string): module name
            debug (bool): True to enable debug, False otherwise
        """
        try:
            if module_name == 'developer':
                self.set_debug(debug)
            elif len(module_name) > 0:
                self.send_command('set_module_debug', 'system', {'module': module_name, 'debug': debug})
        except Exception:
            # module may not exists anymore
            self.logger.exception('Unable to change debug status')

    def create_application(self, module_name):
        """
        Create new application skel

        Args:
            module_name (string): module name

        Raises:
            CommandError: if command failed
        """
        self.__stop_watcher()

        cmd = self.CLI_NEW_APPLICATION_CMD % (self.CLI, module_name)
        self.logger.debug('Create app cmd: %s' % cmd)

        try:
            console = Console()
            res = console.command(cmd, 10.0)
            self.logger.info('Create app cmd result: %s %s' % (res['stdout'], res['stderr']))
            if res['returncode'] != 0:
                raise CommandError('Error during application creation. Check Cleep logs.')

            # sync new app content
            console.command(self.CLI_SYNC_MODULE_CMD % module_name)
        finally:
            self.__start_watcher()

    def __cli_check(self, command, timeout=15.0):
        """
        Execute cleep-cli check specified by command

        Args:
            command (string): cli command to execute

        Returns:
            dict: command output
        """
        console = Console()
        res = console.command(command, timeout)
        self.logger.debug('Cli command "%s" output: %s | %s' % (command, res['stdout'], res['stderr']))
        if res['returncode'] != 0:
            raise CommandError('Command failed')

        try:
            return json.loads(''.join(res['stdout']))
        except Exception as error:
            self.logger.exception('Error parsing command "%s" output' % command)
            raise CommandError('Error parsing check result. Check Cleep logs') from error

    def check_application(self, module_name):
        """
        Check application content

        Args:
            module_name (string): module name

        Returns:
            dict: archive infos::

                {
                    url (string): archive url,
                    name (string): archive name (usually name of module)
                }

        """
        # check parameters
        if module_name is None or len(module_name) == 0:
            raise MissingParameter('Parameter "module_name" is missing')
        module_path = os.path.join(self.cleep_path, 'modules', module_name, '%s.py' % module_name)
        if not os.path.exists(module_path):
            raise InvalidParameter('Module "%s" does not exist' % module_name)

        # execute checks
        backend_result = self.__cli_check(self.CLI_CHECK_BACKEND_CMD % (self.CLI, module_name))
        frontend_result = self.__cli_check(self.CLI_CHECK_FRONTEND_CMD % (self.CLI, module_name))
        scripts_result = self.__cli_check(self.CLI_CHECK_SCRIPTS_CMD % (self.CLI, module_name))
        tests_result = self.__cli_check(self.CLI_CHECK_TESTS_CMD % (self.CLI, module_name))
        # code_result = self.__cli_check(self.CLI_CHECK_CODE_CMD % (self.CLI, module_name))
        changelog_result = self.__cli_check(self.CLI_CHECK_CHANGELOG_CMD % (self.CLI, module_name))

        return {
            'backend': backend_result,
            'frontend': frontend_result,
            'scripts': scripts_result,
            'tests': tests_result,
            'changelog': changelog_result,
            # 'quality': code_result,
        }

    def build_application(self, module_name):
        """
        Build application archive (zip format)
        Archive is not protected by password

        Args:
            module_name (string): module name

        Raises:
            Exception: if build failed
        """
        cmd = self.CLI_BUILD_APP_CMD % (self.CLI, module_name)
        self.logger.debug('Build app cmd: %s' % cmd)

        console = Console()
        res = console.command(cmd, 60.0)
        self.logger.info('Build app result: %s | %s' % (res['stdout'], res['stderr']))
        if res['returncode'] != 0:
            raise CommandError('Error building application. Check Cleep logs.')

        try:
            self.__last_application_build = json.loads(res['stdout'][0])
        except Exception as error:
            self.logger.exception('Error parsing app build command "%s" output' % cmd)
            raise CommandError('Error building application. Check Cleep logs.') from error

    def download_application(self):
        """
        Download latest generated application package

        Returns:
            dict: archive infos::

                {
                    filepath (string): filepath
                    filename (string): filename
                }

        """
        self.logger.debug('Download application archive')
        if not self.__last_application_build:
            raise CommandError('Please build application first')

        return {
            'filepath': self.__last_application_build['package'],
            'filename': os.path.basename(self.__last_application_build['package']),
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
        # send every 10 lines to prevent bus from dropping messages
        if len(self.__tests_buffer) % self.BUFFER_SIZE == 0:
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

        if return_code == 0:
            self.tests_output_event.send(params={'messages': '===== Done ====='}, to='rpc', render=False)
        else:
            self.tests_output_event.send(params={'messages': '===== Tests execution crashes (return code: %s) =====' % return_code}, to='rpc', render=False)

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
        self.tests_output_event.send(params={'messages': 'Tests execution started. Please wait...'}, to='rpc', render=False)

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
        # send every 10 lines to prevent bus from dropping messages
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
        self.docs_output_event.send(params={'messages': 'Documentation generation started. Please wait...'}, to='rpc', render=False)

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


