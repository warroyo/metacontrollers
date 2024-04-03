# Propogate namespace labels to downstream resources

This is a controller that handles propogating labels to downstream resources from the namespace. The resources that the labels are propogated to can be configured in the `label-propogator.yaml`  for example right now Pods are set by default. 

```yaml
resources:
  - apiVersion: v1
    resource: pods
```

This also requires an annotation on the namespace to tell the controller to propogate labels from that namespace. this is currently set to `propogate-labels` you can see an example in the `my-ns.yml`  

all of the code that makes this work are in the following files in the `manifest` directory:

* `kustomization.yml` - used to install this metacontroller function using kustomize
* `label-propogator.yaml` - contains the deployment that runs the python functions and the decoratorcontroller CRD to register it with the metacontroller.This CRD also defines which objects should be watched(Pods by Default).
* `sync.py` -  Python code that handles the controller hooks.


### Prerequisites

* Install [Metacontroller](https://metacontroller.github.io/metacontroller/guide/helm-install.html). For this controller specifically you will need to install `v4.10.2`. The reasonf or this is that there is a bug in the newer versions that prevents the namespace from being used as a related resource. Once this is fixed this repo will be updated. 

### Deploy the DecoratorControllers

```sh
kubectl apply -k manifest
```

### Create an Example namespace

```sh
kubectl apply -f my-ns.yaml
```

Deploy a sample pod

```sh
kubectl run nginx --image=nginx -n test-label-ns
```


Check that the labels are propogated to the pod

```sh
kubectl get pods -n test-label-ns nginx -o json | jq .metadata.labels
```