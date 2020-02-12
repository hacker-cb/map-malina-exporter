# Microart MAP Malina exporter
Prometheus exporter for MAP Malina (http://www.invertor.ru/zzz/item/malina)

## Requirements

```bash
apt install python3-prometheus-client python3-requests
```

## Config

```json
{
    "targets": [
        { "name": "TEST_MAP_1", "host": "192.168.0.2", "login": "username", "password": "password" },
        { "name": "TEST_MAP_2", "host": "192.168.0.3", "login": "username", "password": "password", "timeout": 5 },
        { "name": "TEST_MAP_3", "host": "192.168.0.4" }
    ],
    "timeout" : 1,
    "port": 26001
}
```

Optional values:
 * port (default is 26001)
 * timeout (default is 1s)


## Running

```bash
python3 malina_exporter.py path/to/config.json
```

## Prometheus
```
  - job_name: 'map_malina'
    metrics_path: /metrics
    scrape_interval: 5s
    static_configs:
            - targets: [ 'localhost:26001']

```