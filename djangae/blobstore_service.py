import os
import threading
import logging


blobstore_service = None
server = None


def start_blobstore_service():
    """
        When the blobstore files API was deprecated, the blobstore storage was switched
        to use a POST request to the upload handler when storing files uploaded via Django.

        Unfortunately this breaks in the local sandbox when you aren't running the dev_appserver
        because there is no server to handle the blobstore upload. So, this service is kicked
        off by the local sandbox and only handles blobstore uploads. When runserver kicks in
        this service is stopped.
    """
    global blobstore_service
    global server

    from wsgiref.simple_server import make_server
    from google.appengine.tools.devappserver2.blob_upload import Application

    from djangae.views import internalupload
    from django.core.handlers.wsgi import WSGIRequest
    from django.utils.encoding import force_str

    def handler(environ, start_response):
        request = WSGIRequest(environ)
        response = internalupload(request)

        status = '%s %s' % (response.status_code, response.reason_phrase)
        response_headers = [(str(k), str(v)) for k, v in response.items()]
        start_response(force_str(status), response_headers)
        return response

    port = int(os.environ['SERVER_PORT'])
    logging.info("Starting blobstore service on port %s", port)
    server = make_server('', port, Application(handler))
    blobstore_service = threading.Thread(target=server.serve_forever)
    blobstore_service.daemon = True
    blobstore_service.start()


def stop_blobstore_service():
    global blobstore_service
    global server

    if not blobstore_service:
        return

    server.shutdown()
    blobstore_service.join(5)
    blobstore_service = None