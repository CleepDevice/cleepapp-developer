#!/usr/bin/env python
# -*- coding: utf-8 -*-

from raspiot.libs.internals.event import Event

class DeveloperTestsOutputEvent(Event):
    """
    developer.tests.output event
    """

    EVENT_NAME = u'developer.tests.output'
    EVENT_SYSTEM = True
    EVENT_PARAMS = [u'messages']

    def __init__(self, bus, formatters_broker, events_broker):
        """
        Constructor

        Args:
            bus (MessageBus): message bus instance
            formatters_broker (FormattersBroker): formatters broker instance
            events_broker (EventsBroker): events broker instance
        """
        Event.__init__(self, bus, formatters_broker, events_broker)

