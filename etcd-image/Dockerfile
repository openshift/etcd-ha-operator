FROM registry.access.redhat.com/ubi8/ubi-minimal As FIOBUILDER

RUN microdnf install tar gzip gcc make jq; \
    cd /home; \ 
    curl -O https://github.com/axboe/fio/archive/refs/tags/fio-3.28.tar.gz -L ;\
    tar -xf fio-3.28.tar.gz > /tmp/extraction_logs 2>&1 && tail -n 100 /tmp/extraction_logs; \
    cd /home/fio-fio-3.28  &&\
    ./configure --disable-native> /tmp/configure_logs 2>&1 && tail -n 100 /tmp/configure_logs ;\
    make >/tmp/make_logs 2>&1 && tail -n 100 /tmp/make_logs;\
    make install >/tmp/make_install_logs 2>&1 && tail -n 100 /tmp/make_install_logs


FROM registry.access.redhat.com/ubi8/ubi-minimal

LABEL name="Etcd image" \
      vendor="Openshift" \
      version="3.4.16" \
      summary="etcd3 image for use in etcd-ha-operator"

LABEL description="This is a docker image containing etcd version 3.4.16 on UBI8 to be used in etcd-ha-operator"

COPY licenses /licenses

COPY  --from=FIOBUILDER /usr/local/bin/fio*   /usr/local/bin/ 

COPY scripts/fio/run.sh /tmp/run.sh

RUN set -eux; \
    microdnf update; \
    microdnf install tar hostname bind-utils net-tools jq; \
    microdnf clean all; \
    curl -o /tmp/etcd.tar.gz  https://storage.googleapis.com/etcd/v3.4.16/etcd-v3.4.16-linux-amd64.tar.gz -L;\
    tar -xzvf /tmp/etcd.tar.gz -C /tmp --strip-components=1; \
    mv /tmp/etcd /usr/local/bin/; \
    mv /tmp/etcdctl /usr/local/bin/; \
    rm -rf /tmp/Documentation/ tmp/README* /tmp/etcd.tar.gz; \
    mkdir -p /var/etcd/; \
    mkdir -p /var/lib/etcd/;\
    touch /tmp/fio.out && chmod go+w /tmp/fio.out && chmod g+w /var/lib/etcd
    # Download and build FIO and dependencies

# Alpine Linux doesn't use pam, which means that there is no /etc/nsswitch.conf,
# but Golang relies on /etc/nsswitch.conf to check the order of DNS resolving
# (see https://github.com/golang/go/commit/9dee7771f561cf6aee081c0af6658cc81fac3918)
# To fix this we just create /etc/nsswitch.conf and add the following line:
RUN echo 'hosts: files mdns4_minimal [NOTFOUND=return] dns mdns4' >> /etc/nsswitch.conf

EXPOSE 2379 2380

# Define default command.
CMD ["/usr/local/bin/etcd"]