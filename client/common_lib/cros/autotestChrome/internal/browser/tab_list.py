# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


class TabList(object):

  def __init__(self, tab_list_backend):
    self._tab_list_backend = tab_list_backend

  def New(self, in_new_window=False, timeout=300, url=None):
    """ Open a new browser context.

    Args:
      in_new_window: If true, opens the tab in a popup window. Otherwise, opens
        in current window.
      timeout: The timeout in seconds to wait for the tab to open.
    Returns:
      The Tab object for the newly created tab.
    Raises:
      devtools_http.DevToolsClientConnectionError
      exceptions.EvaluateException: for the current implementation of opening
        a tab in a new window.
    """
    return self._tab_list_backend.New(in_new_window, timeout, url)

  def __iter__(self):
    return self._tab_list_backend.__iter__()

  def __len__(self):
    return self._tab_list_backend.__len__()
