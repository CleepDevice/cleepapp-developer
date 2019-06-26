#!/usr/bin/env python
# -*- coding: utf-8 -*-

from raspiot.events.event import Event

class DeveloperFrontendRestartEvent(Event):
    """
    developer.frontend.restart event
    """

    EVENT_NAME = u'developer.frontend.restart'
    EVENT_SYSTEM = True

    def __init__(self, bus, formatters_broker, events_broker):
        """
        Constructor

        Args:
            bus (MessageBus): message bus instance
            formatters_broker (FormattersBroker): formatters broker instance
            events_broker (EventsBroker): events broker instance
        """
        Event.__init__(self, bus, formatters_broker, events_broker)

    def _check_params(self, params):
        """
        Check event parameters

        Args:
            params (dict): event parameters

        Return:
            bool: True if params are valid, False otherwise
        """
        #no params
        return True
