
if [ ! -f /workspaces/alertmanager-0.28.1.linux-amd64/alertmanager ]; then
  echo Downloading alertmanager...
  curl -Ls https://github.com/prometheus/alertmanager/releases/download/v0.28.1/alertmanager-0.28.1.linux-amd64.tar.gz -o \
    /tmp/alertmanager-0.28.1.linux-amd64.tar.gz

  tar -xf /tmp/alertmanager-0.28.1.linux-amd64.tar.gz -C /workspaces/
  rm /tmp/alertmanager-0.28.1.linux-amd64.tar.gz
fi
/workspaces/alertmanager-0.28.1.linux-amd64/alertmanager --config.file=alertmanager.yml 
