#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import inspect


class Logger(object):
    """
    Logger is a basic structured logger. It is initiated with the path from
    where logging is occuring and any constant values. Constant values can
    later be bound, unbound, or re-bound. Handlers receive a dictionary.
    """

    def __init__(self, path, values=None, handlers=None):
        if values is None:
            values = {}

        if handlers is None:
            handlers = []

        self._values = values
        self._handlers = handlers

        if path is not None:
            self._values['path'] = path

    def bind(self, key, value):
        """
        Bind a new constant or re-bind an existing constant. The key and value
        will appear in all future log statements. If the same key is used in a
        log statement, that value will take precedence over a constant.

        :type key: string
        :param key: The key to bind the value to
        :type value: string
        :param value: The value to be bound to the key
        """
        self._values[key] = value

    def unbind(self, key):
        """
        Unbind a constant. The key will no longer appear in any future log
        statements.

        :type key: string
        :param key: The key to unbind
        """
        del self._values[key]

    def add_handler(self, handler):
        """
        Add a new handler to the logger.

        :type handler: function
        :param handler: The function to add as a handler for the logger
        """
        self._handlers.append(handler)

    def remove_handler(self, handler):
        """
        Remove a handler from the logger. Note: this will remove the first
        instance of the handler - if a handler was added multiple times, only
        a single instance will be removed with each call.

        :type handler: function
        :param handler: The function to remove as a handler from the logger
        """

        if handler in self._handlers:
            self._handlers.remove(handler)

    def _log(self, level, event, values):
        """
        Internal method which adds additional values (e.g. the timestamp, log
        level, etc.) and forwards the result to each handler for processing.

        :type level: string
        :param level: The log level (e.g. debug, info, warning, error, etc.)
        :type event: string
        :param event: The event being logged
        :type values: dict
        :param values: The keys and values associated with the event
        """

        params = self._values.copy()

        if values is not None:
            params.update(values)

        if event is not None:
            params['event'] = event

        params['timestamp'] = datetime.datetime.utcnow()
        params['level'] = level

        if 'path' not in params:
            path = inspect.stack()[2][1]
            path = path[:-3]
            path = path[path.find('tyr'):]
            path = path.replace('/', '.')
            path += '.{function}'.format(function=inspect.stack()[2][3])

            params['path'] = path

        for handler in self._handlers:
            handler(params)

    def debug(self, event=None, values=None):
        """
        Method for logging debug level events.

        :type event: string
        :param event: The event being logged
        :type values: dict
        :param values: The keys and values associated with the event.
        """
        self._log('debug', event, values)

    def info(self, event=None, values=None):
        """
        Method for logging info level events.

        :type event: string
        :param event: The event being logged
        :type values: dict
        :param values: The keys and values associated with the event.
        """
        self._log('info', event, values)

    def warning(self, event=None, values=None):
        """
        Method for logging warning level events.

        :type event: string
        :param event: The event being logged
        :type values: dict
        :param values: The keys and values associated with the event.
        """
        self._log('warning', event, values)

    def error(self, event=None, values=None):
        """
        Method for logging error level events.

        :type event: string
        :param event: The event being logged
        :type values: dict
        :param values: The keys and values associated with the event.
        """
        self._log('error', event, values)

    def critical(self, event=None, values=None):
        """
        Method for logging critical level events.

        :type event: string
        :param event: The event being logged
        :type values: dict
        :param values: The keys and values associated with the event.
        """
        self._log('critical', event, values)
