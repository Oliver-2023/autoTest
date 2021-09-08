# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import six.moves.xmlrpc_server
from six.moves.socketserver import ThreadingMixIn


class MultiThreadedXMLRPCServer(ThreadingMixIn,
                                six.moves.xmlrpc_server.SimpleXMLRPCServer):
    """
    This class simply subclasses SimepleXMLRPCServer and ThreadingMixIn so that
    our XMLRPCSERVER will be multi-threaded and can handle multiple xml-rpc
    requests in parallel.
    """
    pass