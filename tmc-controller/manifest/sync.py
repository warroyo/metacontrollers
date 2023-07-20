#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import time
import requests
import datetime
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

    @refreshToken
    def get_ns_by_cluster(self,object):
        cluster = object['spec']['fullName']['clusterName']
        ns = object['spec']['fullName']['name']
        mgmt = object['spec']['fullName']['managementClusterName']
        prov = object['spec']['fullName']['provisionerName']
        #check if ns exists
        response = requests.get('https://%s/v1alpha1/clusters/%s/namespaces?fullName.managementClusterName=%s&fullName.provisionerName=%s' % (self.tmc_host, cluster,mgmt,prov),headers={'authorization': 'Bearer '+self.access_token})
        response.raise_for_status()
        return response.json()
    
    @refreshToken
    def get_ns_by_name(self,object):
        cluster = object['spec']['fullName']['clusterName']
        ns = object['spec']['fullName']['name']
        mgmt = object['spec']['fullName']['managementClusterName']
        prov = object['spec']['fullName']['provisionerName']
        dt = datetime.datetime.now()
        #check if ns exists
        response = requests.get('https://%s/v1alpha1/clusters/%s/namespaces/%s?fullName.managementClusterName=%s&fullName.provisionerName=%s' % (self.tmc_host, cluster,ns,mgmt,prov),headers={'authorization': 'Bearer '+self.access_token})
        response.raise_for_status()
        return response.json()

    #create a new namespace
    @refreshToken
    def create_ns(self,object):
        cluster = object['spec']['fullName']['clusterName']
        ns = object['spec']['fullName']['name']
        namespace_object = {"namespace": object['spec']}
       

        response = self.get_ns_by_cluster(object)
        if not response:
            raise Exception("cluster namespace response is empty, this may mean the cluster does not exist.")
        
        namespaces = response['namespaces']
        if not namespaces or not any(d['fullName']['name'] == ns for d in namespaces):
            logging.info("namespace does not exist creating "+ ns)
            response = requests.post('https://%s/v1alpha1/clusters/%s/namespaces' % (self.tmc_host, cluster),headers={'authorization': 'Bearer '+self.access_token}, json=namespace_object)
            response.raise_for_status()

        else:
            logging.info("namespace exists updating "+ ns)
            response = requests.put('https://%s/v1alpha1/clusters/%s/namespaces/%s' % (self.tmc_host, cluster,ns),headers={'authorization': 'Bearer '+self.access_token}, json=namespace_object)
            response.raise_for_status()
    
        #for some reason calling the API too quickly after an update cuases it to no return status so we retry
        status_field = {}
        while not status_field:
          logging.info("getting current namespace status") 
          nsstatus = self.get_ns_by_name(object)
          status_field =  nsstatus['namespace']['status']
          time.sleep(2)
        return  {'status': status_field}
    

    @refreshToken
    def delete_ns(self,object):
        cluster = object['spec']['fullName']['clusterName']
        ns = object['spec']['fullName']['name']
        mgmt = object['spec']['fullName']['managementClusterName']
        prov = object['spec']['fullName']['provisionerName']
        response = requests.delete('https://%s/v1alpha1/clusters/%s/namespaces/%s?fullName.managementClusterName=%s&fullName.provisionerName=%s' % (self.tmc_host, cluster,ns,mgmt,prov),headers={'authorization': 'Bearer '+self.access_token})
        response.raise_for_status()

        return {'status': {},"finalized": True}
        

    def do_POST(self):
        if self.path == '/sync':
            dt = datetime.datetime.now()
            observed = json.loads(self.rfile.read(int(self.headers.get('content-length'))))
            try:
                response = self.create_ns(observed['parent'])
            except Exception as e:
                logging.error(e)
                response = {'status': {"phase": "NOT_READY","conditions":{"Ready": {
                    "type": "Ready",
                    "status": "FALSE",
                    "lastTransitionTime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": str(e)
                }} }}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        elif self.path == '/finalize':
            observed = json.loads(self.rfile.read(int(self.headers.get('content-length'))))
            try:
                response = self.delete_ns(observed['parent'])
            except requests.exceptions.HTTPError as e:
                logging.error(e)
                if e.response.status_code != 404:
                    response = {'status': {"phase": "NOT_READY","conditions":{"Ready": {
                        "type": "Ready",
                        "status": "FALSE",
                        "lastTransitionTime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "reason": str(e)
                    }} }}
                else:
                    response = {'status': {},"finalized": True}
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





