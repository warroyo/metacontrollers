# Service Account per Namespace

This is a very basic example of a decorator controller that adds a service account to a namespace based on a label. This example uses jsonnet for simplicity.

all of the cod that makes this work are in the following files in the `manifest` directory:

* `kustomization.yml` - used to install this metacontroller function using kustomize
* `sa-per-ns.yaml` - contains the deployment that runs the jsonnet functions and the decoratorcontroller CRD to register it with the metacontroller.This CRd also defines which objects should be watched and created as well as the label selector to match on.
* `sync.jsonnet` -  jsonnet code that runs when the ns is created, this gets the webhook request from the metacontroller and has access to all details of the ns. it also adds the service account definition to be created.
* `finalize.jsonnet` - this runs when the label on the ns or ns is deleted. it cleans up the service account.


### Prerequisites

* Kubernetes 1.8+ is recommended for its improved CRD support,
  especially garbage collection.
* Install [Metacontroller](https://github.com/metacontroller/metacontroller).

### Deploy the DecoratorControllers

```sh
kubectl apply -k manifest
```

### Create an Example namespace

```sh
kubectl apply -f my-ns.yaml
```

Watch for the service account get created:

```sh
kubectl get sa -n custom-sa-ns --watch
```


Check that the sa gets cleaned up when the ns label is deleted:

```sh
kubeclt label ns custom-sa-ns custom-sa-
kubectl get sa -n custom-sa-ns
```