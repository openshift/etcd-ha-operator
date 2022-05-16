password=$(oc get secret ibm-etcd-instance-auth -o json | jq -r '.data.password')
echo $password | base64 -D
