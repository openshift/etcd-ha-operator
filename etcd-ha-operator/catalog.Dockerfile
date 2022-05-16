FROM registry.redhat.io/openshift4/ose-operator-registry:v4.6 AS builder
FROM registry.redhat.io/ubi8/ubi
COPY bundles.db /database/index.db
LABEL etcd-ha-operator.coreos.com.catalog.version="1.0.0"
LABEL operators.operatorframework.io.index.database.v1=/database/index.db
COPY --from=builder /usr/bin/registry-server /registry-server
COPY --from=builder /bin/grpc_health_probe /bin/grpc_health_probe
EXPOSE 50051
ENTRYPOINT ["/registry-server"]
CMD ["--database", "/database/index.db"]