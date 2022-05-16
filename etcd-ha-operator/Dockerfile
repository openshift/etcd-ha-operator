FROM quay.io/operator-framework/ansible-operator:v1.4.2

USER root

LABEL name="IBM Operator for Etcd" \
      vendor="IBM" \
      com.ibm.license_terms="https://www-03.ibm.com/software/sla/sladb.nsf/search?OpenForm" \
      maintainer="IBM" \
      summary="IBM Operator for Etcd" \
      com.redhat.openshift.versions="v4.5,v4.6" \
      com.redhat.delivery.operator.bundle=true \
      description="IBM Operator for Etcd" 

COPY requirements.yml ${HOME}/requirements.yml

RUN ansible-galaxy collection install -r ${HOME}/requirements.yml \
    && chmod -R ug+rwx ${HOME}/.ansible \
    && yum -y install nss_wrapper \
    && yum -y upgrade --allowerasing --skip-broken --nobest
    
RUN pip3 install --upgrade pip \
    && pip install pyyaml~=3.12 \
    && pip install etcd3-py \
    && mv /usr/local/lib/python3.8/site-packages/etcd3 /usr/local/lib/python3.8/site-packages/etcd3_py \
    && pip install etcd3 \
    && pip install boto3 \
    && pip install botocore

COPY entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod ug+rwx /usr/local/bin/entrypoint.sh

USER ${USER_UID}

COPY licenses /licenses
COPY roles/ ${HOME}/roles/
COPY playbooks/ ${HOME}/playbooks/
COPY watches.yaml ${HOME}/watches.yaml

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
