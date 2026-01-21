#!/bin/bash

# Import popular Kubernetes dashboards to Grafana
GRAFANA_URL="http://grafana.34.173.19.139.nip.io"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin123"

echo "Importing Grafana dashboards..."

# Dashboard IDs from grafana.com
DASHBOARDS=(
  "15760:Kubernetes / Views / Global"
  "15757:Kubernetes / Views / Namespaces"
  "15758:Kubernetes / Views / Nodes"
  "15759:Kubernetes / Views / Pods"
  "315:Kubernetes cluster monitoring (via Prometheus)"
  "3119:Kubernetes Cluster Monitoring"
)

for dashboard in "${DASHBOARDS[@]}"; do
  IFS=':' read -r id name <<< "$dashboard"
  echo "Importing: $name (ID: $id)"
  
  curl -s -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    "$GRAFANA_URL/api/dashboards/import" \
    -d "{
      \"dashboard\": $(curl -s https://grafana.com/api/dashboards/$id/revisions/1/download),
      \"overwrite\": true,
      \"inputs\": [{
        \"name\": \"DS_PROMETHEUS\",
        \"type\": \"datasource\",
        \"pluginId\": \"prometheus\",
        \"value\": \"Prometheus\"
      }]
    }" > /dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo "  ✓ Imported successfully"
  else
    echo "  ✗ Failed to import"
  fi
done

echo ""
echo "Done! Open Grafana and go to Dashboards to see your new dashboards."
echo "URL: $GRAFANA_URL"
