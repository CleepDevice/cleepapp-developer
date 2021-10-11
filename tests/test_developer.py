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
        logging.basicConfig(level=logging.DEBUG, format=u'%(asctime)s %(name)s:%(lineno)d %(levelname)s : %(message)s')
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

if __name__ == '__main__':
    # coverage run --omit="*/lib/python*/*","test_*" --concurrency=thread test_developer.py; coverage report -m -i
    unittest.main()
    
