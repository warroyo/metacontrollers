#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging


logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class Controller(BaseHTTPRequestHandler):

    def update_labels(self,object,related):
        LOGGER.info("Logging related objects ---> {0}".format(related['Namespace.v1']))
        ns_meta = related['Namespace.v1'][object['metadata']['namespace']]['metadata']
        if "annotations" not in ns_meta or "propogate-labels" not in ns_meta["annotations"] :
            LOGGER.info("Namespace is not set to propogate labels  %s", ns_meta['name'])
            return {}
        else:
            LOGGER.info("Namespace is set to propogate labels %s", ns_meta['name'])
            #remove kubernetes.io labels
            LOGGER.info("unfiltered labels %s", ns_meta['labels'])
            filtered_labels = {k:v for k,v in ns_meta['labels'].items() if 'kubernetes.io' not in k}
            LOGGER.info("adding labels %s", filtered_labels)
            return {"labels": filtered_labels}
        


    def customize(self,parent) -> dict:
        return [
            {
                'apiVersion': 'v1',
                'resource': 'namespaces',
                'names': [parent['metadata']['namespace']]
            }
        ]
   
    def do_POST(self):
        if self.path == '/sync':
            observed = json.loads(self.rfile.read(int(self.headers.get('content-length'))))
            LOGGER.info("/sync %s", observed['object']['metadata']['name'])
            labels = self.update_labels(observed['object'], observed['related']) 
            response = labels
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        elif self.path == '/customize':
            request: dict = json.loads(self.rfile.read(
                int(self.headers.get('content-length'))))
            parent: dict = request['parent']
            LOGGER.info("/customize %s", parent['metadata']['name'])
            LOGGER.info("Parent resource: \n %s", parent['spec'])
            related_resources: dict = {
                'relatedResources': self.customize(parent)
            }
            LOGGER.info("Related resources: \n %s", related_resources)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(related_resources).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg: dict = {
                'error': '404',
                'endpoint': self.path
            }
            self.wfile.write(json.dumps(error_msg).encode('utf-8'))

HTTPServer(('', 80), Controller).serve_forever()



