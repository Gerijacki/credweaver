# CUPP v2 — Kubernetes Deployment Guide

This directory contains all Kubernetes manifests needed to run CUPP v2 wordlist generation jobs in a cluster.

## Prerequisites

- A running Kubernetes cluster (minikube, k3s, GKE, EKS, AKS, etc.)
- `kubectl` configured and pointing at your cluster
- The `cupp-v2:latest` Docker image available to the cluster (pushed to a registry or loaded locally)
- A StorageClass named `standard` that can provision `ReadWriteOnce` volumes (or edit `pvc.yaml` to match your cluster)

To verify your cluster is reachable:
```bash
kubectl cluster-info
kubectl get nodes
```

## Image Availability

The job manifests reference `cupp-v2:latest`. Make the image available to your cluster before applying:

**Local cluster (minikube / k3s):**
```bash
# minikube
minikube image load cupp-v2:latest

# k3s
docker save cupp-v2:latest | sudo k3s ctr images import -
```

**Remote cluster (push to registry first):**
```bash
docker tag cupp-v2:latest registry.example.com/cupp-v2:latest
docker push registry.example.com/cupp-v2:latest
# Then update the image field in job.yaml and cronjob.yaml accordingly
```

## Applying All Manifests

Apply manifests in dependency order:

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create PersistentVolumeClaim for output
kubectl apply -f k8s/pvc.yaml

# 3. Create ConfigMap with CUPP configuration
kubectl apply -f k8s/configmap.yaml

# 4. (Optional) Run a one-shot generation job
kubectl apply -f k8s/job.yaml

# 5. (Optional) Schedule nightly generation
kubectl apply -f k8s/cronjob.yaml
```

Or apply everything at once:
```bash
kubectl apply -f k8s/
```

## Providing a Target Profile via ConfigMap

The job expects a profile file at `/profiles/target.yaml` inside the container. Provide it through a separate ConfigMap named `cupp-profiles`:

```bash
# Create ConfigMap from your profile file
kubectl create configmap cupp-profiles \
  --from-file=target.yaml=profiles/example_target.yaml \
  --namespace cupp-v2

# Or from multiple profiles
kubectl create configmap cupp-profiles \
  --from-file=profiles/ \
  --namespace cupp-v2
```

You can also write a ConfigMap manifest directly:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cupp-profiles
  namespace: cupp-v2
data:
  target.yaml: |
    name: "john"
    surname: "doe"
    birthdate:
      day: 15
      month: 6
      year: 1990
    pet_name: "rex"
    company: "acme"
    keywords:
      - "security"
```

Apply it:
```bash
kubectl apply -f my-profile-configmap.yaml
```

## Running a One-Shot Job

```bash
# Apply the job
kubectl apply -f k8s/job.yaml

# Watch the job status
kubectl get job cupp-generate -n cupp-v2 --watch

# Stream logs from the running pod
kubectl logs -n cupp-v2 -l app=cupp-v2,component=generator -f

# Check completion
kubectl describe job cupp-generate -n cupp-v2
```

## Monitoring the Job

```bash
# Get pod status
kubectl get pods -n cupp-v2 -l component=generator

# Describe the job for events and status
kubectl describe job cupp-generate -n cupp-v2

# View logs (replace <pod-name> with actual pod name)
kubectl logs -n cupp-v2 <pod-name>

# Watch all resources in the namespace
kubectl get all -n cupp-v2 --watch
```

## Retrieving Output from the PVC

The generated wordlist is written to the PVC at `/output/wordlist.txt`. To retrieve it:

**Method 1: Use a temporary pod**
```bash
kubectl run -n cupp-v2 pvc-reader \
  --image=busybox \
  --restart=Never \
  --overrides='{
    "spec": {
      "volumes": [{"name":"output","persistentVolumeClaim":{"claimName":"cupp-output-pvc"}}],
      "containers": [{"name":"pvc-reader","image":"busybox",
        "command":["sleep","3600"],
        "volumeMounts":[{"name":"output","mountPath":"/output"}]}]
    }
  }'

# Copy out the wordlist
kubectl cp -n cupp-v2 pvc-reader:/output/wordlist.txt ./wordlist.txt

# Clean up
kubectl delete pod -n cupp-v2 pvc-reader
```

**Method 2: Mount PVC into a Job that uploads to object storage**

Write a post-processing Job that reads `/output/wordlist.txt` and uploads it to S3/GCS, then applies it after the generation job completes.

## Scheduled Generation (CronJob)

The `cronjob.yaml` manifest schedules generation at 02:00 UTC every night.

```bash
# Apply
kubectl apply -f k8s/cronjob.yaml

# List scheduled runs
kubectl get cronjob -n cupp-v2

# Manually trigger a run now
kubectl create job -n cupp-v2 --from=cronjob/cupp-scheduled cupp-manual-$(date +%s)

# View history
kubectl get jobs -n cupp-v2
```

To change the schedule, edit the `spec.schedule` field in `cronjob.yaml` using standard cron syntax.

## Scaling Considerations

**Memory**: The default limit is 2 Gi for a single job. The Bloom filter for 10M capacity at 0.1% error rate uses approximately 14 MB. The working set for streaming generation is constant; memory scales only with bloom filter size.

**CPU**: The Rust engine uses a single thread for generation. The `cpu: "4"` limit gives room for the OS scheduler; reduce to `cpu: "2"` on resource-constrained clusters.

**Parallelism**: For parallel wordlist generation against multiple targets, create multiple Jobs (one per target profile ConfigMap) — they can run concurrently as long as they write to separate output paths. Use `spec.parallelism` if you want Kubernetes to run multiple pods for the same job.

**Storage**: A deep aggressive-preset run can produce hundreds of millions of passwords. At ~10 bytes per password, 100M passwords is ~1 GB. Adjust `pvc.yaml` storage size accordingly.

## Cleaning Up

```bash
# Delete a completed job
kubectl delete job cupp-generate -n cupp-v2

# Delete the cronjob
kubectl delete cronjob cupp-scheduled -n cupp-v2

# Delete everything in the namespace
kubectl delete namespace cupp-v2
```

Deleting the namespace also deletes the PVC and all data in it. Copy outputs before deleting.
