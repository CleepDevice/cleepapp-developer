import unittest
import logging
import sys
import time
sys.path.append('../')
from backend.developer import Developer
from cleep.exception import InvalidParameter, MissingParameter, CommandError, Unauthorized
from cleep.libs.tests import session
from unittest.mock import Mock, DEFAULT, patch

class TestDeveloper(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.FATAL, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
        self.session = session.TestSession(self)

    def tearDown(self):
        self.session.clean()

    def init(self, start_module=True):
        self.module = self.session.setup(Developer)
        if start_module:
            self.session.start_module(self.module)

    def mock_get_config_field(self, mock_by_fields):
        if 'devices' not in mock_by_fields:
            mock_by_fields['devices'] = {}

        def my_mock(field):
            logging.debug('Request _get_config_field(%s)' % field)
            if field in mock_by_fields:
                return mock_by_fields[field]
            return DEFAULT

        return my_mock

    def test_configure_moduleindev(self):
        self.init(False)
        self.module._get_config_field = Mock(side_effect=self.mock_get_config_field({'moduleindev': 'test'}))

        self.session.start_module(self.module)

        self.module.cleep_filesystem.enable_write.assert_called_with(root=True, boot=True)

    def test_configure_add_device(self):
        self.init(False)
        devices = {
            '1234567890': {
                'type': 'developer',
            }
        }
        self.module.get_module_devices = Mock(side_effect=[devices])
        self.module._get_config_field = Mock(side_effect=self.mock_get_config_field({'devices': devices, 'moduleindev': None}))
        self.module._get_device_count = Mock(return_value=0)
        self.module._add_device = Mock()

        self.session.start_module(self.module)

        self.assertTrue(self.module._add_device.called)
        self.assertIsNotNone(self.module._Developer__developer_uuid)

    def test_configure_device_already_exists(self):
        self.init(False)
        devices = {
            '1234567890': {
                'type': 'developer',
            }
        }
        self.module.get_module_devices = Mock(side_effect=[devices])
        self.module._get_config_field = Mock(side_effect=self.mock_get_config_field({'devices': devices, 'moduleindev': None}))
        self.module._get_device_count = Mock(return_value=1)
        self.module._add_device = Mock()

        self.session.start_module(self.module)

        self.assertFalse(self.module._add_device.called)
        self.assertIsNotNone(self.module._Developer__developer_uuid)

    def test_on_start(self):
        self.init(False)
        self.module._Developer__launch_watcher = Mock()
        
        self.session.start_module(self.module)

        self.assertTrue(self.module._Developer__launch_watcher.called)

    def test_on_stop(self):
        self.init(False)
        self.module._Developer__watcher_task = Mock()
        self.module._Developer__tests_task = Mock()
        self.module._Developer__docs_task = Mock()
        self.module._Developer__launch_watcher = Mock()
        self.module._Developer__launch_tests = Mock()
        self.module._Developer__generate_documentation = Mock()

        self.session.start_module(self.module)
        self.module._on_stop()
        
        self.assertTrue(self.module._Developer__watcher_task.stop.called)
        self.assertTrue(self.module._Developer__tests_task.stop.called)
        self.assertTrue(self.module._Developer__docs_task.stop.called)

    @patch('backend.developer.Console')
    @patch('backend.developer.EndlessConsole')
    def test_launch_watcher(self, endless_console_mock, console_mock):
        self.init()

        self.module._Developer__launch_watcher()

        console_mock.return_value.command.assert_called()
        endless_console_mock.return_value.start.assert_called()

    def test_watcher_callback(self):
        self.init(False)
        self.module._Developer__watcher_task = Mock()
        self.module._Developer__launch_watcher = Mock()
        self.module.logger = Mock()

        self.session.start_module(self.module)
        self.module._Developer__watcher_callback('stdout', 'stderr')

        self.module.logger.error.assert_called_with('Error on watcher: stdout stderr')

    def test_watcher_end_callback(self):
        self.init(False)
        self.module._Developer__watcher_task = Mock()
        self.module._Developer__tests_task = Mock()
        self.module._Developer__launch_watcher = Mock()
        self.module.logger = Mock()

        self.session.start_module(self.module)
        self.module._Developer__watcher_end_callback(666, True)
        
        self.module.logger.error.assert_called()
        self.session.assert_event_called('developer.tests.output')
        self.assertEqual(self.module._Developer__launch_watcher.call_count, 2)

    def test_get_module_devices(self):
        self.init(True)

        devices = self.module.get_module_devices()
        logging.debug('Devices: %s' % devices)

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[list(devices.keys())[0]]['type'], 'developer')

    def test_restart_frontend(self):
        self.init()

        self.module.restart_frontend()

        self.session.assert_event_called('developer.frontend.restart')

    def test_select_application_for_development(self):
        self.init()
        self.module._get_config_field = Mock(side_effect=self.mock_get_config_field({'moduleindev': 'test'}))
        self.module._set_config_field = Mock()
        self.module._Developer__set_module_debug = Mock()

        self.module.select_application_for_development('dummy')

        self.module._Developer__set_module_debug.assert_any_call('test', False)
        self.module._Developer__set_module_debug.assert_any_call('dummy', True)
        self.module.cleep_filesystem.enable_write.assert_any_call(root=True, boot=True)
        self.module.cleep_filesystem.disable_write.assert_not_called()

    def test_select_application_for_development_disable_dev(self):
        self.init()
        self.module._get_config_field = Mock(side_effect=self.mock_get_config_field({'moduleindev': 'test'}))
        self.module._set_config_field = Mock()
        self.module._Developer__set_module_debug = Mock()

        self.module.select_application_for_development(None)

        self.module._Developer__set_module_debug.assert_called_once()
        self.module.cleep_filesystem.enable_write.assert_not_called()
        self.module.cleep_filesystem.disable_write.assert_called_with(root=True, boot=True)

    def test_set_module_debug_enable(self):
        self.init()
        set_module_debug_cmd_mock = self.session.make_mock_command('set_module_debug')
        self.session.add_mock_command(set_module_debug_cmd_mock)
        self.module.set_debug = Mock()

        self.module._Developer__set_module_debug('test', True)

        self.session.command_called_with('set_module_debug', {'module': 'test', 'debug': True}, 'system')
        self.module.set_debug.assert_not_called()

    def test_set_module_debug_disable(self):
        self.init()
        set_module_debug_cmd_mock = self.session.make_mock_command('set_module_debug')
        self.session.add_mock_command(set_module_debug_cmd_mock)
        self.module.set_debug = Mock()

        self.module._Developer__set_module_debug('test', False)

        self.session.command_called_with('set_module_debug', {'module': 'test', 'debug': False}, 'system')
        self.module.set_debug.assert_not_called()

    def test_set_module_debug_enable_developer(self):
        self.init()
        set_module_debug_cmd_mock = self.session.make_mock_command('set_module_debug')
        self.session.add_mock_command(set_module_debug_cmd_mock)
        self.module.set_debug = Mock()

        self.module._Developer__set_module_debug('developer', True)

        self.assertFalse(self.session.command_called('set_module_debug'))
        self.module.set_debug.assert_called()

    def test_set_module_debug_exception(self):
        self.init()
        self.module.send_command = Mock(side_effect=Exception('Test exception'))
        self.module.logger = Mock()

        try:
            self.module._Developer__set_module_debug('test', True)
        except:
            self.fail('Should handle exception')
        self.module.logger.exception.assert_called_with('Unable to change debug status')

    @patch('backend.developer.Console')
    def test_create_application(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'returncode': 0, 'stdout': 'stdout', 'stderr': 'stderr'}

        self.module.create_application('test')

        console_mock.return_value.command.assert_called()

    @patch('backend.developer.Console')
    def test_create_application_exception(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'returncode': 1, 'stdout': 'stdout', 'stderr': 'stderr'}

        with self.assertRaises(Exception) as cm:
            self.module.create_application('test')
        self.assertEqual(str(cm.exception), 'Error during application creation. Check Cleep logs.')

    @patch('backend.developer.Console')
    def test_cli_check(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'stdout': ['{"hello": "world"}'], 'stderr': 'stderr'}

        result = self.module._Developer__cli_check('a command')
        logging.debug('Result: %s' % result)

        self.assertEqual(result, {'hello': 'world'})

    @patch('backend.developer.Console')
    def test_cli_check_invalid_json(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'stdout': ['{hello: "world"}'], 'stderr': 'stderr'}

        with self.assertRaises(CommandError) as cm:
            self.module._Developer__cli_check('a command')
        self.assertEqual(str(cm.exception), 'Error parsing check result. Check Cleep logs.')

    def test_check_application(self):
        self.init()
        self.module._Developer__cli_check = Mock(return_value='result')

        with patch('backend.developer.os.path.exists') as os_path_exists:
            os_path_exists.return_value = True
            result = self.module.check_application('dummy')
            logging.debug('Result: %s' % result)

        self.assertEqual(result, {
            'backend': 'result',
            'frontend': 'result',
            'scripts': 'result',
            'tests': 'result',
            'changelog': 'result',
        })
        self.assertEqual(self.module._Developer__cli_check.call_count, 5)

    def test_check_application_invalid_params(self):
        self.init()

        with patch('backend.developer.os.path.exists') as os_path_exists:
            os_path_exists.return_value = False
            with self.assertRaises(InvalidParameter) as cm:
                self.module.check_application('dummy')
            self.assertEqual(str(cm.exception), 'Module "dummy" does not exist')

        with self.assertRaises(MissingParameter) as cm:
            self.module.check_application('')
        self.assertEqual(str(cm.exception), 'Parameter "module_name" is missing')

    @patch('backend.developer.Console')
    def test_build_application(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'returncode': 0, 'stdout': ['{"hello": "world"}'], 'stderr': 'stderr'}

        try:
            self.module.build_application('dummy')
        except:
            self.fail('It should not fails')

    @patch('backend.developer.Console')
    def test_build_application_failed(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'returncode': 2, 'stdout': ['{"hello": "world"}'], 'stderr': 'stderr'}

        with self.assertRaises(CommandError) as cm:
            self.module.build_application('dummy')
        self.assertEqual(str(cm.exception), 'Error building application. Check Cleep logs.')

    @patch('backend.developer.Console')
    def test_build_application_invalid_command_response(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'returncode': 0, 'stdout': ['{hello: "world"}'], 'stderr': 'stderr'}

        with self.assertRaises(CommandError) as cm:
            self.module.build_application('dummy')
        self.assertEqual(str(cm.exception), 'Error building application. Check Cleep logs.')

    def test_download_application(self):
        self.init()
        self.module._Developer__last_application_build = {'package': '/tmp/package/path/cleepapp_dummy.zip'}

        result = self.module.download_application()

        self.assertEqual(result, {
            'filepath': '/tmp/package/path/cleepapp_dummy.zip',
            'filename': 'cleepapp_dummy.zip',
        })

    def test_download_application_no_build(self):
        self.init()
        self.module._Developer__last_application_build = None

        with self.assertRaises(CommandError) as cm:
            self.module.download_application()
        self.assertEqual(str(cm.exception), 'Please build application first')

    def test_tests_callback(self):
        self.init()
        self.module._Developer__tests_task = Mock()

        for i in range(self.module.BUFFER_SIZE):
            self.module._Developer__tests_callback('stdout', 'stderr')
        params = self.session.get_last_event_params('developer.tests.output')
        logging.debug('Params: %s' % params)

        self.assertEqual(self.session.event_call_count('developer.tests.output'), 1)
        self.assertEqual(params['messages'], ['stdoutstderr'] * 10)

    def test_tests_end_callback(self):
        self.init()
        self.module._Developer__tests_task = Mock()
        self.module._Developer__tests_buffer = ['stdout'] * 5

        self.module._Developer__tests_end_callback(0, False)
        params = self.session.get_last_event_params('developer.tests.output')
        logging.debug('Params: %s' % params)

        self.assertEqual(self.session.event_call_count('developer.tests.output'), 2)
        self.assertEqual(params['messages'], '===== Done =====')
        self.assertEqual(len(self.module._Developer__tests_buffer), 0)

    def test_tests_end_callback_failed(self):
        self.init()
        self.module._Developer__tests_task = Mock()
        self.module._Developer__tests_buffer = ['stdout'] * 5

        self.module._Developer__tests_end_callback(1, False)
        params = self.session.get_last_event_params('developer.tests.output')
        logging.debug('Params: %s' % params)

        self.assertEqual(self.session.event_call_count('developer.tests.output'), 2)
        self.assertEqual(params['messages'], '===== Tests execution crashes (return code: 1) =====')
        self.assertEqual(len(self.module._Developer__tests_buffer), 0)

    @patch('backend.developer.EndlessConsole')
    def test_launch_tests(self, endless_console_mock):
        self.init()

        self.module.launch_tests('dummy')

        endless_console_mock.return_value.start.assert_called()

    def test_launch_tests_already_running(self):
        self.init()
        self.module._Developer__tests_task = Mock()

        with self.assertRaises(CommandError) as cm:
            self.module.launch_tests('dummy')
        self.assertEqual(str(cm.exception), 'Tests are already running')

    @patch('backend.developer.EndlessConsole')
    def test_get_last_coverage_report(self, endless_console_mock):
        self.init()

        self.module.get_last_coverage_report('dummy')

        endless_console_mock.return_value.start.assert_called()

    def test_get_last_coverage_report_tests_running(self):
        self.init()
        self.module._Developer__tests_task = Mock()

        with self.assertRaises(CommandError) as cm:
            self.module.get_last_coverage_report('dummy')
        self.assertEqual(str(cm.exception), 'Tests are running. Please wait end of it')

    def test_docs_callback(self):
        self.init()
        self.module._Developer__docs_task = Mock()

        for i in range(self.module.BUFFER_SIZE):
            self.module._Developer__docs_callback('stdout', 'stderr')
        params = self.session.get_last_event_params('developer.docs.output')
        logging.debug('Params: %s' % params)

        self.assertEqual(self.session.event_call_count('developer.docs.output'), 1)
        self.assertEqual(params['messages'], ['stdoutstderr'] * 10)

    def test_docs_end_callback(self):
        self.init()
        self.module._Developer__docs_task = Mock()
        self.module._Developer__docs_buffer = ['stdout'] * 5

        self.module._Developer__docs_end_callback(0, False)
        params = self.session.get_last_event_params('developer.docs.output')
        logging.debug('Params: %s' % params)

        self.assertEqual(self.session.event_call_count('developer.docs.output'), 1)
        self.assertEqual(params['messages'], ['stdout'] * 5)
        self.assertEqual(len(self.module._Developer__docs_buffer), 0)

    @patch('backend.developer.EndlessConsole')
    def test_generate_documentation(self, endless_console_mock):
        self.init()

        self.module.generate_documentation('dummy')

        endless_console_mock.return_value.start.assert_called()

    def test_generate_documentation_already_running(self):
        self.init()
        self.module._Developer__docs_task = Mock()

        with self.assertRaises(CommandError) as cm:
            self.module.generate_documentation('dummy')
        self.assertEqual(str(cm.exception), 'Doc generation is running. Please wait end of it')

    @patch('backend.developer.Console')
    def test_download_documentation(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'returncode': 0, 'stdout': ['DOC_ARCHIVE=/tmp/cleep/documentation/dummy.zip'], 'stderr': ['']}

        result = self.module.download_documentation('dummy')
        logging.debug('Result: %s' % result)

        self.assertEqual(result, {
            'filepath': '/tmp/cleep/documentation/dummy.zip',
            'filename': 'dummy.zip',
        })

    @patch('backend.developer.Console')
    def test_download_documentation_failed(self, console_mock):
        self.init()
        console_mock.return_value.command.return_value = {'returncode': 1, 'stdout': ['error'], 'stderr': ['']}

        with self.assertRaises(CommandError) as cm:
            self.module.download_documentation('dummy')
        self.assertEqual(str(cm.exception), 'error')


if __name__ == '__main__':
    # coverage run --omit="*/lib/python*/*","test_*" --concurrency=thread test_developer.py; coverage report -m -i
    unittest.main()
    
