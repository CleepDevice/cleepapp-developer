#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cleep.libs.internals.event import Event

class DeveloperDocsOutputEvent(Event):
    """
    developer.docs.output event
    """

    EVENT_NAME = 'developer.docs.output'
    EVENT_PROPAGATE = False
    EVENT_PARAMS = ['messages']

    def __init__(self, params):
        """
        Constructor

        Args:
            params (dict): event parameters
        """
        Event.__init__(self, params)

