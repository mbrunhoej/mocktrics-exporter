

if [ ! -f /workspaces/prometheus-3.6.0-rc.0.linux-amd64/prometheus ]; then
  echo Downloading prometheus...
  curl -Ls https://github.com/prometheus/prometheus/releases/download/v3.6.0-rc.0/prometheus-3.6.0-rc.0.linux-amd64.tar.gz -o \
    /tmp/prometheus-3.6.0-rc.0.linux-amd64.tar.gz

  tar -xf /tmp/prometheus-3.6.0-rc.0.linux-amd64.tar.gz -C /workspaces/
  rm /workspaces/prometheus-3.6.0-rc.0.linux-amd64
fi
/workspaces/prometheus-3.6.0-rc.0.linux-amd64/prometheus --config.file=prometheus.yml 