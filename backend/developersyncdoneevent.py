#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event


class DeveloperSyncDoneEvent(Event):
    """
    developer.sync.done event
    """

    EVENT_NAME = "developer.sync.done"
    EVENT_PROPAGATE = False
    EVENT_PARAMS = []

    def __init__(self, params):
        """
        Constructor
        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)
