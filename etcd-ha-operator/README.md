## etcd-ha-operator

This project aims to provide a way to deploy etcd in High Availability mode.  It uses `statefulsets` to deploy etcd.

`Note: This operator does not work alongside coreos/etcd-operator because its CRDs are compatible. In order to try this operator please make sure to deploy both the operators in namespaced mode and in different namespaces.`

### Pre-requisites for trying it out:

A kubernetes cluster deployed with `kubectl` correctly configured. [Minikube](https://github.com/kubernetes/minikube/) is the easiest way to get started.

The stateful sets use persistent volumes, the cluster needs to be configured with a dynamic persistent volume provisioner. In case of minikube, the guidelines can be found [here](https://github.com/kubernetes/minikube/blob/master/docs/persistent_volumes.md)

### Steps to build and deploy the operator

1. $ cd ibm-etcd-operator/stable/ibm-etcd-operator-bundle/operators/ibm-etcd-operator

2. $ export OPERATOR_IMG="cp.stg.icr.io/cp/watson/operators/ibm-etcd-operator:hari-142"

2. $ make docker-build docker-push IMG=$OPERATOR_IMG

3. $ make deploy IMG=$OPERATOR_IMG 

4. $ kubectl apply -f config/samples/etcd_v1beta3_etcdcluster.yaml

<!-- ### Steps to bring an etcd cluster up

To follow this guide, make sure you are in the `default` namespace.

1. Create RBAC `kubectl create -f deploy/rbac.yaml`
2. Create CRD `kubectl create -f deploy/crds/crd.yaml`
3. Create EtcdRestore CRD `kubectl create -f deploy/crds/restore_crd.yaml`
4. Create EtcdBackup CRD `kubectl create -f deploy/crds/backup_crd.yaml`
5. Deploy the operator `kubectl create -f deploy/operator.yaml`
6. Create an etcd cluster `kubectl create -f deploy/cr.yaml`
7. Verify that cluster is up by `kubectl get pods -l app=etcd`. You should see something like this

   ```bash
   $ kubectl get pods -l app=etcd
   NAME                     READY   STATUS    RESTARTS   AGE
   example-etcd-cluster-0   1/1     Running   0          27s
   example-etcd-cluster-1   1/1     Running   0          21s
   example-etcd-cluster-2   1/1     Running   0          18s
   ```
 -->
### Accessing the etcd cluster

If you are using minikube:

1. Create a service to access etcd cluster from outside the cluster by `kubectl create -f https://raw.githubusercontent.com/coreos/etcd-operator/master/example/example-etcd-cluster-nodeport-service.json`
2. Install [etcdctl](https://coreos.com/etcd/docs/latest/getting-started-with-etcd.html)
3. Set etcd version `export ETCDCTL_API=3`
4. Set etcd endpoint `export ETCDCTL_ENDPOINTS=$(minikube service example-etcd-cluster-client-service --url)`
5. Set a key in etcd `etcdctl put hello world`

If you are inside the cluster, set the etcd endpoint to: `http://<cluster-name>-client.<namespace>.svc:2379` and it should work. If you are using secure client, use `https` protocol for the endpoint.

### Check failure recovery

Recovering from loss of all the pods is the key purpose behind the idea of using stateful set to deploy etcd. Here are the steps to check it out:

1. Bring an etcd cluster up.
2. Insert some data into the etcd cluster `$etcdctl put hello world`
3. Watch members of etcd cluster by running `watch etcdctl member list` in a separate terminal. You need to export environment variables(ETCDCTL_ENDPOINTS)
4. Delete all the pods to simulate failure recovery `$kubectl delete pod -l app=etcd `
5. Within sometime, you should see all the pods going away and being replaced by a new pods, something like this.
6. After sometime, the cluster will be available again.
7. Check if the data exists:

```bash
$ etcdctl get hello
hello
world
```

### Delete a cluster

1. Bring a cluster up.
2. Delete the cluster by `kubectl delete etcdcluster example-etcd-cluster`. This should delete all the pods and services created because of this cluster

### Restore a cluster

This project only supports restoring a cluster from S3 bucket right now. To restore you will need the AWS `config` and `credentials` [file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html). Place the config and credentials file in a directory and run following commands to create a secret:

```bash
$ export AWS_DIR="/path/to/aws/credentials"
$ cat $AWS_DIR/credentials
[default]
aws_access_key_id = XXX
aws_secret_access_key = XXX

$ cat $AWS_DIR/config
[default]
region = <region>

$ kubectl create secret generic aws --from-file=$AWS_DIR/credentials --from-file=$AWS_DIR/config
```

Run the following commands to create the EtcdCluster CR, replacing `mybucket/etcd.backup` with the full path of the backup file:

```bash
$ wget https://raw.githubusercontent.com/openshift/etcd-ha-operator/master/deploy/restore_cr.yaml
$ sed -e 's|<full-s3-path>|mybucket/etcd.backup|g' \
    -e 's|<aws-secret>|aws|g' \
    restore_cr.yaml \
    | kubectl create -f -
```

This will start the restore process, wait till the `status.phase` of EtcdRestore cr is `Complete` with the following command:

```bash
$ kubectl get -w etcdrestore example-etcd-cluster -o jsonpath='{.status.phase}'
```

### Backup a cluster

This project only supports backing up on S3 bucket right now. To backup you will need the AWS `config` and `credentials` [file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html). Place the config and credentials file in a directory and run following commands to create a secret:

```bash
$ export AWS_DIR="/path/to/aws/credentials"
$ cat $AWS_DIR/credentials
[default]
aws_access_key_id = XXX
aws_secret_access_key = XXX

$ cat $AWS_DIR/config
[default]
region = <region>

$ kubectl create secret generic aws --from-file=$AWS_DIR/credentials --from-file=$AWS_DIR/config
```

Run the following commands to backup the EtcdCluster CR, replacing `mybucket/etcd.backup` with the full path of the backup file, `<etcd-cluster-name>` with the EtcdCluster CR name and  `<namespace>` with namespace of the EtcdCluster CR:

```bash
$ wget https://raw.githubusercontent.com/openshift/etcd-ha-operator/master/deploy/backup_cr.yaml
$ sed -e 's|<full-s3-path>|mybucket/etcd.backup|g' \
    -e 's|<aws-secret>|aws|g' \
    -e 's|<etcd-cluster-endpoints>|"http://<etcd-cluster-name>-client.<namespace>.svc.cluster.local:2379"|g' \
    example/etcd-backup-operator/backup_cr.yaml \
    | kubectl create -f -
```

### TLS certs for the cluster

The operator assumes that the admin has created TLS certificates and corresponding secrets for the EtcdCluster CR. For trying out, run the following commands to create certificates for `example-etcd-cluster`

```bash
$ docker run -it -e USERNAME=$(id -un) -e HOME=$HOME --entrypoint /bin/bash -u $(id -u):0 -w $(pwd) -v $HOME:$HOME:Z quay.io/operator-framework/ansible-operator  -c 'echo "${USERNAME}:x:$(id -u):$(id -g)::${HOME}:/bin/bash" >>/etc/passwd && bash'
$ ansible-playbook tls_playbook.yaml
exit
```

Now, create EtcdCluster CR with TLS enabled with `kubectl create -f deploy/cr_tls.yaml`

If running against an existing cluster, e. g. a Fyre cluster, only this command is needed to create the certs and keys.

```bash
$ ansible-playbook tls_playbook.yaml
```

Now, create EtcdCluster CR with TLS enabled with `kubectl create -f deploy/cr_tls.yaml`

Then you need to log into the pod container and run commands below, e. g. to list the members.

```bash
$ oc exec -it example-etcd-cluster-0 -c etcd sh
$ ETCDCTL_API=3 etcdctl --endpoints=https://[client-endpoint]:2379 --debug --cert=/etc/etcdtls/operator/etcd-tls/etcd-client.crt --key=/etc/etcdtls/operator/etcd-tls/etcd-client.key --cacert=/etc/etcdtls/operator/etcd-tls/etcd-client-ca.crt member list -w table
exit
```

Replace [client-endpoint] with any of the below format.

localhost<br />
*.example-etcd-cluster.default.svc<br />
*.example-etcd-cluster.default.svc.cluster.local<br />
example-etcd-cluster-client<br />
example-etcd-cluster-client.default<br />
example-etcd-cluster-client.default.svc<br />
example-etcd-cluster-client.default.svc.cluster.local<br />

### SecurityContextConstraints Requirements
The predefined SCC name `restricted` has been verified for this chart. If your target namespace is bound to this SCC, you can proceed to install the chart.

Custom SecurityContextConstraints definition:
```
allowHostDirVolumePlugin: false
allowHostIPC: false
allowHostNetwork: false
allowHostPID: false
allowHostPorts: false
allowPrivilegeEscalation: true
allowPrivilegedContainer: false
allowedCapabilities: null
apiVersion: security.openshift.io/v1
defaultAddCapabilities: null
fsGroup:
  type: MustRunAs
kind: SecurityContextConstraints
metadata:
  annotations:
    kubernetes.io/description: restricted denies access to all host features and requires
      pods to be run with a UID, and SELinux context that are allocated to the namespace.  This
      is the most restrictive SCC and it is used by default for authenticated users.
  name: restricted
priority: null
readOnlyRootFilesystem: false
requiredDropCapabilities:
- KILL
- MKNOD
- SETUID
- SETGID
runAsUser:
  type: MustRunAsRange
seLinuxContext:
  type: MustRunAs
supplementalGroups:
  type: RunAsAny
users: []
volumes:
- configMap
- downwardAPI
- emptyDir
- persistentVolumeClaim
- projected
- secret

```

## Redhat Certification Proof

[opencontent-etcd-operator](https://connect.redhat.com/project/5913031/images)

## Storage Options

- OCS ceph-rbd 
- Portworx 
- IBM block gold 

## Platform Delivery Models Supported 

- On premises 
- IBM Cloud/ROKS

## Backup and Restore 

- Note the current size of EtcdCluster 
- Set the size to 0 in EtcdCluster CR 
- Wait for the statefulset to go to 0/0 replicas 
- Go through the backup process
- Set size of EtcdCluster CR to what it was before setting it to 0. Setting a different size will cause the etcdcluster to crash. 

## Create TLS secret using Certificate Manager

1. Install Cert manager and create an issuer 

2. Sample Certificate CR to be used to create tls certs for Etcdcluster 

  - Instance Name: ibm-etcd-instance
  - Namespace: zen 
  - Issuer Name: cs-ca-issuer
  - Secret Name: ibm-etcd-instance-tls

```yaml 
apiVersion: certmanager.k8s.io/v1alpha1
kind: Certificate
metadata:
  name: ibm-etcd-instance-certificate
spec:
  secretName: ibm-etcd-instance-tls
  dnsNames:
  - "localhost"
  - "*.ibm-etcd-instance.zen.svc"
  - "*.ibm-etcd-instance.zen.svc.cluster.local"
  - "ibm-etcd-instance.zen.svc"
  - "ibm-etcd-instance-client"
  - "ibm-etcd-instance-client.zen"
  - "ibm-etcd-instance-client.zen.svc"
  - "ibm-etcd-instance-client.zen.svc.cluster.local"
  issuerRef:
    name: cs-ca-issuer
    # We can reference ClusterIssuers by changing the kind here.
    # The default value is Issuer (i.e. a locally namespaced Issuer)
    kind: Issuer
  duration: 2160h0m0s
  renewBefore: 720h0m0s
```
3. Pass the secret name ibm-etcd-instance-tls in the EtcdCluster CR as below. 

```yaml 
  TLS:
    enableClientCertAuth: false
    static:  
      member:
        peerSecret: "ibm-etcd-instance-tls"
        serverSecret: "ibm-etcd-instance-tls"
      operatorSecret: "ibm-etcd-instance-tls"
```

## Push a new patch fix release

1. Update the CSV version, CSV name, olm skip range, replaces, CASE version, and push it to master branch.
2. Create a semver tagged release in master branch - this will build the operator, bundle and catalog images with the semver tag provided. 
3. Use the newly built images in the resources.yaml, inventory files - nativeDeploy, catalog_source, bundle/CSV. 
4. Push the code to master branch and create a GA release. 
