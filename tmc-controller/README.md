## TMC Controller

This is a controller that handles managing TMC resources.


### Current APIs Supported

* Namespaces -  full LCM of TMC managed namespaces

### Prerequisites

* Install [Metacontroller](https://github.com/metacontroller/metacontroller)

### Deploy the controller

```sh
kubectl apply -k v1
```
(or pass `v1beta1` for kubernetes 1.15 or older)

### Create an TMC namespace

```sh
kubectl apply -f example-ns.yaml
```