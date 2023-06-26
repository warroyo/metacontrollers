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
kubectl create secret generic tmcinfo -n metacontroller --from-literal=CSP_TOKEN=$CSP_TOKEN --from-literal=TMC_HOST=$TMC_HOST 
```

```sh
kubectl apply -k v1
```
(or pass `v1beta1` for kubernetes 1.15 or older)

### Create an TMC namespace


```sh
kubectl apply -f example-ns.yaml
```