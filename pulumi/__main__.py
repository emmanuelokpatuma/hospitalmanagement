"""
Hospital Management GCP Infrastructure with Pulumi
Creates: GKE cluster, node pools, VPC, and necessary configurations
"""

import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s
from pulumi import Config, Output, export

# Load configuration
config = Config()
gcp_config = Config("gcp")

project_id = gcp_config.require("project")
region = gcp_config.get("region") or "us-central1"
zone = gcp_config.get("zone") or "us-central1-a"
cluster_name = config.get("cluster-name") or "hospital-gke"
node_count = config.get_int("node-count") or 3
machine_type = config.get("machine-type") or "e2-standard-2"

# Enable required GCP APIs
services = [
    "container.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
    "cloudresourcemanager.googleapis.com",
]

enabled_services = []
for service in services:
    enabled_service = gcp.projects.Service(
        f"enable-{service.split('.')[0]}",
        service=service,
        project=project_id,
        disable_on_destroy=False,
    )
    enabled_services.append(enabled_service)

# Create VPC Network
network = gcp.compute.Network(
    "hospital-vpc",
    auto_create_subnetworks=False,
    project=project_id,
    opts=pulumi.ResourceOptions(depends_on=enabled_services),
)

# Create Subnet
subnet = gcp.compute.Subnetwork(
    "hospital-subnet",
    ip_cidr_range="10.0.0.0/24",
    region=region,
    network=network.id,
    secondary_ip_ranges=[
        {
            "range_name": "pods",
            "ip_cidr_range": "10.1.0.0/16",
        },
        {
            "range_name": "services",
            "ip_cidr_range": "10.2.0.0/16",
        },
    ],
    project=project_id,
)

# Create GKE Cluster
cluster = gcp.container.Cluster(
    cluster_name,
    name=cluster_name,
    project=project_id,
    location=zone,
    remove_default_node_pool=True,
    initial_node_count=1,
    network=network.name,
    subnetwork=subnet.name,
    ip_allocation_policy={
        "cluster_secondary_range_name": "pods",
        "services_secondary_range_name": "services",
    },
    workload_identity_config={
        "workload_pool": f"{project_id}.svc.id.goog",
    },
    addons_config={
        "http_load_balancing": {"disabled": False},
        "horizontal_pod_autoscaling": {"disabled": False},
        "gce_persistent_disk_csi_driver_config": {"enabled": True},
    },
    monitoring_config={
        "enable_components": ["SYSTEM_COMPONENTS"],
        "managed_prometheus": {"enabled": True},
    },
    logging_config={
        "enable_components": ["SYSTEM_COMPONENTS", "WORKLOADS"],
    },
    opts=pulumi.ResourceOptions(depends_on=[subnet]),
)

# Create Node Pool
node_pool = gcp.container.NodePool(
    "hospital-node-pool",
    cluster=cluster.name,
    location=zone,
    project=project_id,
    node_count=node_count,
    node_config={
        "preemptible": False,
        "machine_type": machine_type,
        "disk_size_gb": 50,
        "disk_type": "pd-standard",
        "oauth_scopes": [
            "https://www.googleapis.com/auth/cloud-platform",
        ],
        "workload_metadata_config": {
            "mode": "GKE_METADATA",
        },
        "metadata": {
            "disable-legacy-endpoints": "true",
        },
        "labels": {
            "environment": "dev",
            "app": "hospital-management",
        },
    },
    management={
        "auto_repair": True,
        "auto_upgrade": True,
    },
    opts=pulumi.ResourceOptions(depends_on=[cluster]),
)

# Create kubeconfig
def generate_kubeconfig(cluster_name, cluster_endpoint, cluster_ca):
    return f"""apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {cluster_ca}
    server: https://{cluster_endpoint}
  name: {cluster_name}
contexts:
- context:
    cluster: {cluster_name}
    user: {cluster_name}
  name: {cluster_name}
current-context: {cluster_name}
kind: Config
preferences: {{}}
users:
- name: {cluster_name}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      installHint: Install gke-gcloud-auth-plugin for use with kubectl by following
        https://cloud.google.com/blog/products/containers-kubernetes/kubectl-auth-changes-in-gke
      provideClusterInfo: true
"""

kubeconfig = Output.all(cluster.name, cluster.endpoint, cluster.master_auth.cluster_ca_certificate).apply(
    lambda args: generate_kubeconfig(args[0], args[1], args[2])
)

# Create Kubernetes provider
k8s_provider = k8s.Provider(
    "gke-k8s",
    kubeconfig=kubeconfig,
    opts=pulumi.ResourceOptions(depends_on=[node_pool]),
)

# Export outputs
export("cluster_name", cluster.name)
export("cluster_endpoint", cluster.endpoint)
export("kubeconfig", kubeconfig)
export("network_name", network.name)
export("subnet_name", subnet.name)
export("project_id", project_id)
export("region", region)
export("zone", zone)

# Deploy applications only (comment out monitoring for now to test)
from apps import deploy_applications
# from monitoring import deploy_monitoring_stack, deploy_logging_stack, deploy_argocd

# Deploy applications first
apps = deploy_applications(k8s_provider)

# Export additional outputs
export("hospital_namespace", apps["namespace"].metadata["name"])

# TODO: Uncomment after apps are working
# monitoring = deploy_monitoring_stack(k8s_provider)
# logging = deploy_logging_stack(k8s_provider)
# argocd = deploy_argocd(k8s_provider)
