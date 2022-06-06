# Installation der Filter und Weigher

Die Filter und Weigher müssen im Python Namespace des Nova Scheduler Dienstes verfügbar sein. Zusätzlich muss für die Extra Spec Validierung der Entrypoint **nova.api.extra_spec_validators** für den Nova API Dienst sichtbar sein.

## Installation der Filter und Weigher unter OpenStack Kolla

### 1. Installation des Pakets

Dieses Projekt beinhaltet ein eigenes Installationsskript: [install.sh](/install.sh)

Dabei wird das Projekt automatisch gebaut und ein Python-Paket erzeugt und in den Nova API und Scheduler Container installiert.

Das Skript muss mit dem SSH User und Hostname/IP des Controllers aufgerufen werden. Es empfielt sich vorher den SSH Public Key auf den Controller einzutragen, um die Passwortabfrage zu umgehen.

Einzelner Controller:
```bash
./install.sh root@controller
```

Mehrere Controller (HA):
```bash
./install.sh root@controller1 root@controller2 root@controller3 ...
```

### 2. Konfiguration von OpenStack Kolla

Nachdem das Paket installiert ist, muss OpenStack Kolla konfiguriert werden, damit die eigenen Filter und Weigher genutzt werden.

Dafür wird die Datei **/etc/kolla/config/nova/nova-scheduler.conf** mit folgendem Inhalt angelegt:

```ini
[filter_scheduler]
available_filters = nova.scheduler.filters.all_filters
enabled_filters = ComputeFilter,AvailabilityZoneFilter,ComputeCapabilitiesFilter,ImagePropertiesFilter,ServerGroupAntiAffinityFilter,ServerGroupAffinityFilter,AggregateInstanceExtraSpecsFilter
weight_classes = schedulerbuilder.nova.weighers.virtual_weigher.GpuVirtualWeigher
```

Anschließend muss Nova neu konfiguriert werden.

```bash
kolla-ansible -i ./multinode reconfigure --tag nova
```

## Installation von eigenen Filtern und Weigher in Nova Scheduler

1. Das eigene Paket muss auf den Controllern (Nova API & Nova Scheduler) installiert sein.

2. Konfiguration der Filter und Weigher in **/etc/nova/nova.conf**.

    - Filter:

        ```ini
        [filter_scheduler]
        available_filters = nova.scheduler.filters.all_filters # filters shipped with Nova
        available_filters = mypackage.filters.SingleInstancePerRequestFilter # Custom filter
        enabled_filters = ComputeFilter,SingleInstancePerRequestFilter
        ```

    - Weigher:

        ```ini
        [filter_scheduler]
        weight_classes = mypackage.weighers.InstanceCountWeigher
        ```

Nach dem Neustart der Dienste **nova-api** und **nova-scheduler** sind die Filter und Weigher aktiviert.
