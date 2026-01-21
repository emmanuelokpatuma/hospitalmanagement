"""
Kubernetes application deployments
Deploys Hospital Management services using Helm charts
"""

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts
import os

def deploy_applications(k8s_provider):
    """Deploy all Hospital Management applications"""
    
    # Get absolute path to helm chart
    chart_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hpm"))
    
    # Create namespace
    namespace = k8s.core.v1.Namespace(
        "hospital-namespace",
        metadata={"name": "hospital"},
        opts=pulumi.ResourceOptions(provider=k8s_provider),
    )
    
    # Deploy SQL Server
    sqlserver = Chart(
        "hospital-sqlserver",
        ChartOpts(
            chart=chart_path,
            namespace=namespace.metadata["name"],
            values={
                "replicaCount": 0,
                "sqlserver": {"enabled": True},
                "image": {
                    "repository": "hospital-frontend",
                    "tag": "latest",
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[namespace],
        ),
    )
    
    # Deploy Patient API
    patient_api = Chart(
        "hospital-patient-api",
        ChartOpts(
            chart=chart_path,
            namespace=namespace.metadata["name"],
            values={
                "image": {
                    "repository": "patient-api",
                    "tag": "latest",
                    "pullPolicy": "IfNotPresent",
                },
                "service": {
                    "port": 3000,
                    "type": "ClusterIP",
                },
                "env": [
                    {"name": "DB_SERVER", "value": "hospital-sqlserver-hpm-sqlserver"},
                ],
                "sqlserver": {"enabled": False},
                "replicaCount": 2,
                "metrics": {"enabled": True, "path": "/metrics"},
                "resources": {
                    "limits": {"cpu": "500m", "memory": "512Mi"},
                    "requests": {"cpu": "250m", "memory": "256Mi"},
                },
                "livenessProbe": {
                    "httpGet": {"path": "/health", "port": 3000},
                    "initialDelaySeconds": 30,
                    "periodSeconds": 10,
                },
                "readinessProbe": {
                    "httpGet": {"path": "/health", "port": 3000},
                    "initialDelaySeconds": 10,
                    "periodSeconds": 5,
                },
                "podAnnotations": {
                    "prometheus.io/scrape": "true",
                    "prometheus.io/port": "3000",
                    "prometheus.io/path": "/metrics",
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[sqlserver],
        ),
    )
    
    # Deploy Appointment API
    appointment_api = Chart(
        "hospital-appointment-api",
        ChartOpts(
            chart=chart_path,
            namespace=namespace.metadata["name"],
            values={
                "image": {
                    "repository": "appointment-api",
                    "tag": "latest",
                    "pullPolicy": "IfNotPresent",
                },
                "service": {
                    "port": 3001,
                    "type": "ClusterIP",
                },
                "env": [
                    {"name": "DB_SERVER", "value": "hospital-sqlserver-hpm-sqlserver"},
                ],
                "sqlserver": {"enabled": False},
                "replicaCount": 2,
                "metrics": {"enabled": True, "path": "/metrics"},
                "resources": {
                    "limits": {"cpu": "500m", "memory": "512Mi"},
                    "requests": {"cpu": "250m", "memory": "256Mi"},
                },
                "livenessProbe": {
                    "httpGet": {"path": "/health", "port": 3001},
                    "initialDelaySeconds": 30,
                    "periodSeconds": 10,
                },
                "readinessProbe": {
                    "httpGet": {"path": "/health", "port": 3001},
                    "initialDelaySeconds": 10,
                    "periodSeconds": 5,
                },
                "podAnnotations": {
                    "prometheus.io/scrape": "true",
                    "prometheus.io/port": "3001",
                    "prometheus.io/path": "/metrics",
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[sqlserver],
        ),
    )
    
    # Deploy Frontend
    frontend = Chart(
        "hospital-frontend",
        ChartOpts(
            chart=chart_path,
            namespace=namespace.metadata["name"],
            values={
                "image": {
                    "repository": "hospital-frontend",
                    "tag": "latest",
                    "pullPolicy": "IfNotPresent",
                },
                "service": {
                    "port": 80,
                    "type": "LoadBalancer",
                },
                "replicaCount": 2,
                "sqlserver": {"enabled": False},
                "resources": {
                    "limits": {"cpu": "200m", "memory": "256Mi"},
                    "requests": {"cpu": "100m", "memory": "128Mi"},
                },
                "livenessProbe": {
                    "httpGet": {"path": "/", "port": 80},
                    "initialDelaySeconds": 10,
                    "periodSeconds": 10,
                },
                "readinessProbe": {
                    "httpGet": {"path": "/", "port": 80},
                    "initialDelaySeconds": 5,
                    "periodSeconds": 5,
                },
            },
        ),
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[patient_api, appointment_api],
        ),
    )
    
    return {
        "namespace": namespace,
        "sqlserver": sqlserver,
        "patient_api": patient_api,
        "appointment_api": appointment_api,
        "frontend": frontend,
    }
