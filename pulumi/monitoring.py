"""
Monitoring and Logging Stack
Deploys Prometheus, Grafana, Elasticsearch, and Kibana
"""

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts

def deploy_monitoring_stack(k8s_provider):
    """Deploy Prometheus and Grafana using kube-prometheus-stack"""
    
    # Create monitoring namespace
    monitoring_ns = k8s.core.v1.Namespace(
        "monitoring",
        metadata={"name": "monitoring"},
        opts=pulumi.ResourceOptions(provider=k8s_provider),
    )
    
    # Deploy kube-prometheus-stack
    prometheus_stack = Chart(
        "kube-prometheus-stack",
        ChartOpts(
            chart="kube-prometheus-stack",
            version="55.0.0",
            namespace=monitoring_ns.metadata["name"],
            fetch_opts=FetchOpts(
                repo="https://prometheus-community.github.io/helm-charts",
            ),
            values={
                "prometheus": {
                    "prometheusSpec": {
                        "retention": "7d",
                        "storageSpec": {
                            "volumeClaimTemplate": {
                                "spec": {
                                    "accessModes": ["ReadWriteOnce"],
                                    "resources": {"requests": {"storage": "10Gi"}},
                                }
                            }
                        },
                        "additionalScrapeConfigs": [
                            {
                                "job_name": "patient-api",
                                "kubernetes_sd_configs": [
                                    {
                                        "role": "pod",
                                        "namespaces": {"names": ["hospital"]},
                                    }
                                ],
                                "relabel_configs": [
                                    {
                                        "source_labels": ["__meta_kubernetes_pod_annotation_prometheus_io_scrape"],
                                        "regex": "true",
                                        "action": "keep",
                                    },
                                    {
                                        "source_labels": ["__meta_kubernetes_pod_annotation_prometheus_io_path"],
                                        "target_label": "__metrics_path__",
                                        "regex": "(.+)",
                                    },
                                    {
                                        "source_labels": ["__address__", "__meta_kubernetes_pod_annotation_prometheus_io_port"],
                                        "regex": "([^:]+)(?::\\d+)?;(\\d+)",
                                        "replacement": "$1:$2",
                                        "target_label": "__address__",
                                    },
                                ],
                            }
                        ],
                    },
                    "service": {
                        "type": "LoadBalancer",
                    },
                },
                "grafana": {
                    "adminPassword": "admin123",
                    "service": {
                        "type": "LoadBalancer",
                    },
                    "persistence": {
                        "enabled": True,
                        "size": "5Gi",
                    },
                },
                "alertmanager": {
                    "enabled": True,
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[monitoring_ns],
        ),
    )
    
    return {
        "namespace": monitoring_ns,
        "prometheus_stack": prometheus_stack,
    }


def deploy_logging_stack(k8s_provider):
    """Deploy Elasticsearch and Kibana for centralized logging"""
    
    # Create logging namespace
    logging_ns = k8s.core.v1.Namespace(
        "logging",
        metadata={"name": "logging"},
        opts=pulumi.ResourceOptions(provider=k8s_provider),
    )
    
    # Deploy Elasticsearch
    elasticsearch = Chart(
        "elasticsearch",
        ChartOpts(
            chart="elasticsearch",
            version="8.5.1",
            namespace=logging_ns.metadata["name"],
            fetch_opts=FetchOpts(
                repo="https://helm.elastic.co",
            ),
            values={
                "replicas": 1,
                "minimumMasterNodes": 1,
                "resources": {
                    "requests": {
                        "cpu": "500m",
                        "memory": "1Gi",
                    },
                    "limits": {
                        "cpu": "1000m",
                        "memory": "2Gi",
                    },
                },
                "volumeClaimTemplate": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {
                        "requests": {
                            "storage": "30Gi",
                        },
                    },
                },
                "persistence": {
                    "enabled": True,
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[logging_ns],
        ),
    )
    
    # Deploy Kibana
    kibana = Chart(
        "kibana",
        ChartOpts(
            chart="kibana",
            version="8.5.1",
            namespace=logging_ns.metadata["name"],
            fetch_opts=FetchOpts(
                repo="https://helm.elastic.co",
            ),
            values={
                "service": {
                    "type": "LoadBalancer",
                },
                "resources": {
                    "requests": {
                        "cpu": "500m",
                        "memory": "512Mi",
                    },
                    "limits": {
                        "cpu": "1000m",
                        "memory": "1Gi",
                    },
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[elasticsearch],
        ),
    )
    
    # Deploy Filebeat for log collection
    filebeat = Chart(
        "filebeat",
        ChartOpts(
            chart="filebeat",
            version="8.5.1",
            namespace=logging_ns.metadata["name"],
            fetch_opts=FetchOpts(
                repo="https://helm.elastic.co",
            ),
            values={
                "daemonset": {
                    "enabled": True,
                },
                "filebeatConfig": {
                    "filebeat.yml": """
filebeat.inputs:
- type: container
  paths:
    - /var/log/containers/*.log
  processors:
    - add_kubernetes_metadata:
        host: ${NODE_NAME}
        matchers:
        - logs_path:
            logs_path: "/var/log/containers/"

output.elasticsearch:
  hosts: ['elasticsearch-master:9200']
  indices:
    - index: "filebeat-patient-api-%{+yyyy.MM.dd}"
      when.contains:
        kubernetes.labels.app: patient-api
    - index: "filebeat-appointment-api-%{+yyyy.MM.dd}"
      when.contains:
        kubernetes.labels.app: appointment-api
    - index: "filebeat-frontend-%{+yyyy.MM.dd}"
      when.contains:
        kubernetes.labels.app: hospital-frontend
"""
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[elasticsearch],
        ),
    )
    
    return {
        "namespace": logging_ns,
        "elasticsearch": elasticsearch,
        "kibana": kibana,
        "filebeat": filebeat,
    }


def deploy_argocd(k8s_provider):
    """Deploy ArgoCD for GitOps"""
    
    # Create argocd namespace
    argocd_ns = k8s.core.v1.Namespace(
        "argocd",
        metadata={"name": "argocd"},
        opts=pulumi.ResourceOptions(provider=k8s_provider),
    )
    
    # Deploy ArgoCD
    argocd = Chart(
        "argocd",
        ChartOpts(
            chart="argo-cd",
            version="5.51.0",
            namespace=argocd_ns.metadata["name"],
            fetch_opts=FetchOpts(
                repo="https://argoproj.github.io/argo-helm",
            ),
            values={
                "server": {
                    "service": {
                        "type": "LoadBalancer",
                    },
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[argocd_ns],
        ),
    )
    
    return {
        "namespace": argocd_ns,
        "argocd": argocd,
    }
