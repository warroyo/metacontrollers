#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import time
import requests
import os

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

 #get access token from CSP token
def getAccessToken(csp_host,csp_token):
    try:
        response = requests.post('https://%s/csp/gateway/am/api/auth/api-tokens/authorize?refresh_token=%s' % (csp_host,csp_token))
        response.raise_for_status()
    except Exception as e:
        logging.error(e)
        return None
    else:
        access_token = response.json()['access_token']
        expires_in = response.json()['expires_in']
        expire_time = time.time() + expires_in
        return access_token, expire_time

class Controller(BaseHTTPRequestHandler):
    csp_token = None
    access_token = None
    access_token_expiration = None
    csp_host = None
    tmc_host = os.environ["TMC_HOST"]

    logging.info("getting initial token")
    csp_token = os.environ['CSP_TOKEN']
    csp_host = "console.cloud.vmware.com"
    try:
        access_token, access_token_expiration = getAccessToken(csp_host,csp_token)
        if access_token is None:
            raise Exception("Request for access token failed.")
    except Exception as e:
        logging.error(e)
    else:
        logging.info("access token recieved")
        
   
    #decorator function for rereshing token
    def refreshToken(decorated):
        def wrapper(api,*args,**kwargs):
            if time.time() > api.access_token_expiration:
                api.access_token, api.access_token_expiration =  getAccessToken(api.csp_host,api.csp_token)
                Controller.update_token(api.access_token,api.access_token_expiration)
            return decorated(api,*args,**kwargs)

        return wrapper
    
    #function to update the class levels api token so it can be re-used
    @classmethod    
    def update_token(cls,access_token, expire_time):
        cls.access_token =access_token
        cls.access_token_expiration = expire_time


    #create a new namespace
    @refreshToken
    def create_ns(self,object):
        cluster = object['spec']['fullName']['clusterName']
        ns = object['spec']['fullName']['name']
        namespace_object = {"namespace": object['spec']}
        #check if ns exists
        try:
            response = requests.get('https://%s/v1alpha1/clusters/%s/namespaces' % (self.tmc_host, cluster),headers={'authorization': 'Bearer '+self.access_token})
            response.raise_for_status()
        except Exception as e:
            logging.error(e)
            return 
        
        namespaces = response.json()['namespaces']
        if not namespaces or not any(d['fullName']['name'] == ns for d in namespaces):
            try:
                response = requests.post('https://%s/v1alpha1/clusters/%s/namespaces' % (self.tmc_host, cluster),headers={'authorization': 'Bearer '+self.access_token}, json=namespace_object)
                response.raise_for_status()
            except Exception as e:
                logging.error(e)
                return

        else:
            try:
                response = requests.put('https://%s/v1alpha1/clusters/%s/namespaces/%s' % (self.tmc_host, cluster,ns),headers={'authorization': 'Bearer '+self.access_token}, json=namespace_object)
                response.raise_for_status()
            except Exception as e:
                logging.error(e)
                return
 
    @refreshToken
    def delete_ns(self,object):
        cluster = object['spec']['fullName']['clusterName']
        ns = object['spec']['fullName']['name']
        mgmt = object['spec']['fullName']['managementClusterName']
        prov = object['spec']['fullName']['provisionerName']
        try:
            response = requests.delete('https://%s/v1alpha1/clusters/%s/namespaces/%s?fullName.managementClusterName=%s&fullName.provisionerName=%s' % (self.tmc_host, cluster,ns,mgmt,prov),headers={'authorization': 'Bearer '+self.access_token})
            response.raise_for_status()
        except Exception as e:
            logging.error(e)
            return 

    def do_POST(self):
        if self.path == '/sync':
            observed = json.loads(self.rfile.read(int(self.headers.get('content-length'))))
            self.create_ns(observed['parent'])

            response: dict = {
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif self.path == '/finalize':
            observed = json.loads(self.rfile.read(int(self.headers.get('content-length'))))
            self.delete_ns(observed['parent'])
            response: dict = {
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
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





