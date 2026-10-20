#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class DeveloperSyncStartedEvent(Event):
    """
    developer.sync.started event
    """

    EVENT_NAME = "developer.sync.started"
    EVENT_PROPAGATE = False
    EVENT_PARAMS = []

    def __init__(self, params):
        """
        Constructor
        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
