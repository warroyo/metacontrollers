function(request) {
  local ns = request.object,

  // Create a service account for the namespace
  attachments: [
    {
      apiVersion: "v1",
      kind: "ServiceAccount",
      metadata: {
        namespace: ns.metadata.name,
        name: ns.metadata.name + "-custom-sa",
        labels: {"created-by": "sa-per-ns"}
      }
    }
  ]
}