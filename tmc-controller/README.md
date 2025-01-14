## TMC Controller

This is a controller that handles managing TMC resources.


### Current APIs Supported

* Namespaces -  full LCM of TMC managed namespaces

### Prerequisites

* Install [Metacontroller](https://github.com/metacontroller/metacontroller)

### Deploy the controller
Deploy the secret that containes the TMC api token, this is retrieved from the CSP console.

```sh
export CSP_TOKEN='<csp token here>'
export TMC_HOST='yourtmchost.com'
export DRY_RUN='true or false' # this will prevent any TMC call from being made
kubectl create secret generic tmcinfo -n metacontroller --from-literal=CSP_TOKEN=$CSP_TOKEN --from-literal=TMC_HOST=$TMC_HOST --from-literal=DRY_RUN=$DRY_RUN
```

```sh
kubectl apply -k v1
```
(or pass `v1beta1` for kubernetes 1.15 or older)

### Create an TMC namespace


```sh
kubectl apply -f example-ns.yaml
```


## API Spec

## TMCNamespace

this CRD alows for creating a TMC namespace in a workspace. 

```yaml
apiVersion: tmc.tanzufield.vmware.com/v1
kind: TMCNamespace
metadata:
  name: #name of the resource in the cluster
  annotations:
    tmc-controller.upsert-only: "true" # optional annotation to prevent delete of the upstream TMC namespace if this is set. should be use for production in most cases
  labels:
    version: v1
spec:
  fullName:
    clusterName: # name of the cluster
    managementClusterName: # name of the TMC mgmt cluster
    name: #name of the namespace 
    provisionerName: #name of the TMC provisioner
  meta:
    labels: {} # any arbitrary labels to add
  spec:
    workspaceName: # the tmc workspace
```