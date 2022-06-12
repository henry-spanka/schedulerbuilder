# Erweiterung von Nova um Filter und Weigher

Der OpenStack Compute Dienst Nova nutzt Filter und Weigher zur Zuweisung von Instanzen auf Hosts.

Dabei werden in einem ersten Schritt die Compute Hosts der OpenStack Cloud vom Dienst Nova Scheduler gefiltert und eine Liste von möglichen Kanidaten erstellt (Filter) [[1]](#quelle_1). Im zweiten Schritt wird diese Liste dann gewichtet um den bestmöglichen Compute Host zu finden (Weigher).

![Nova Scheduler](assets/filtering-workflow-1.png)

Filter und Weigher bestehen dabei aus jeweils einer Python-Klasse die dann vom Nova Scheduler aufgerufen wird (Entrypoint).

Es empfiehlt sich die Klassen in ein eigenes Paket zu packen damit diese auf den jeweiligen Nodes installiert, aktualisiert und versioniert werden können.

In diesem Projekt sind die Filter unter **/src/schedulerbuilder/nova/filters** und Weigher unter **/src/schedulerbuilder/nova/weighers** zu finden.

## Filter

Ein Filter besteht aus der Funktion **host_passes**. Dabei kann der **HostState** und der **RequestSpec** zur Entscheidung genutzt werden ob die Instanz auf den Host scheduled werden darf. Dies ist dann der Fall, wenn alle Filter für den jeweiligen Host **True** zurückgeben.

```python
from nova.objects.request_spec import RequestSpec
from nova.scheduler.host_manager import HostState
from nova.scheduler import filters

class SingleInstancePerRequestFilter(filters.BaseHostFilter):
   RUN_ON_REBUILD = False

   def host_passes(self, host_state: HostState, request_spec: RequestSpec):
      # Only allow user to schedule a single instance at a time
      return request_spec.num_instances == 1
```

Im obigen Beispiel wurde ein Filter implementiert, der es nur erlaubt eine einzelne Instanz pro Request zu erstellen.

## Weigher

Ein Weigher besteht aus den zwei Funktionen **weight_multiplier** und **_weigh_object**.

### weigh_object

Gewichtet eine geplante Instanz. Dabei kann der **HostState** und der **RequestSpec** der Instanz zur Gewichtung genutzt werden.
Rückgabewert ist dabei das Gewicht als Float.

Dabei gilt:

- Gewicht > 0: Host wird priorisiert.
- Gewicht = 0: Weigher nimmt keinen Einfluss aufs Scheduling.
- Gewicht < 0: Gewicht des Hosts wird reduziert.

### weight_multiplier

Das ermittelte normalisierte Gewicht von **weigh_object** wird mit dem Rückgabewert dieser Funktion multipliziert. Dabei kann der **HostState** zur Berechnung genutzt werden. Dadurch können Weigher uneinander unterschiedlich gewichtet oder deaktiviert werden.

### Kombination von Weighern

Alle Weigher ermitteln unabhängig ein Gewicht. Diese werden dann zwischen 0 und 1 normalisiert und wie folgt kombiniert [[2]](#quelle_2):

   `weight = w1_multiplier * norm(w1) + w2_multiplier * norm(w2) + ...`

Der Multiplier ist dabei der Rückgabewert der Funktion **weigh_multiplier**.

Dabei gilt:

- Multiplier > 0: Einfluss des Weighers wird verstärkt.
- Multiplier = 0: Weigher nimmt keinen Einfuss aufs Scheduling.
- Multiplier < 0: Einfluss des Weighers wird reduziert.

Ein Weigher gewichtet eine Liste von Compute Nodes. Daher ist es nicht möglich im Nachhinein einen Host vom Scheduling zu exkludieren. Dafür muss ein Filter vorgeschaltet werden.

```python
from nova.scheduler import weights
from nova.scheduler.host_manager import HostState
from nova.objects.request_spec import RequestSpec

class InstanceCountWeigher(weights.BaseHostWeigher):
    def weight_multiplier(self, host_state: HostState):
        """Override the weight multiplier."""
        return utils.get_weight_multiplier(
            host_state, 'instance_count_weight_multiplier',
            1.0)

    def _weigh_object(self, host_state: HostState, request_spec: RequestSpec):
       return host_state.num_instances # Stack based on Instances
```

Im Beispiel ist ein Weigher implementiert, der einen Host anhand seiner Instanzen gewichtet. Dadurch werden Hosts mit mehr Instanzen priorisiert (Stacking). Über die Metadata der Host Aggregates (instance_count_weight_multiplier) kann dann die Wichtigkeit des Weighers bestimmt werden. Ein negatives Gewicht fürt dabei zu einem Spreading, d.h. die Instanzen werden möglichst breit auf den Hosts verteilt.

### HostState und RequestSpec

Während der Filterung bzw. Gewichtung können die Klassen **HostState** und **RequestSpec** genutzt werden.

#### HostState

Beschreibt den Zustand der Compute Node. Die Klasse besitzt dabei unter anderem die folgenden Eigenschaften:

- **nodename**: Name des Compute Hosts
- **total_usable_ram_mb**: Gesamter RAM in MB
- **total_usable_disk_gb**: Gesamter Festplattenspeicher in GB
- **disk_mb_used**: Genutzter Festplattenspeicher in MB
- **free_ram_mb**: Freier RAM in MB
- **free_disk_mb**: Freier Festplattenspeicher in MB
- **vcpus_total**: Gesamte Anzahl an vCPUs
- **vcpus_used**: Genutzte Anzahl an vCPUs
- **pci_stats**: Informationen über die verfügbare PCI Hardware
- **num_instances**: Anzahl Instanzen auf dem Host
- **cpu_info**: Prozessoreigenschaften
- **instances**: Liste der Instanzen des Hosts

Die gesamte Liste an verfügbaren Eigenschaften ist hier einsehbar: [https://github.com/openstack/nova/blob/stable/yoga/nova/scheduler/host_manager.py#L97](https://github.com/openstack/nova/blob/stable/yoga/nova/scheduler/host_manager.py#L97)

#### RequestSpec

Das **RequestSpec** beschreibt die Anforderungen der Instanz, unter anderem:

- **image**: Image der Instanz
- **pci_requests**: Angeforderte PCI Hardware
- **flavor**: Flavor der Instanz
- **num_instances**: Anzahl der angeforderten Instanzen

Alle Eigenschaften sind einsehbar unter: [https://github.com/openstack/nova/blob/stable/yoga/nova/objects/request_spec.py#L42](https://github.com/openstack/nova/blob/stable/yoga/nova/objects/request_spec.py#L42)

#### Weitere

Die Eigenschaften **HostState** und **RequestSpec** beinhalten teilweise Unterklassen. Dabei sind besonders nützlich:

- **Instance**: [https://github.com/openstack/nova/blob/stable/yoga/nova/objects/instance.py#L107](https://github.com/openstack/nova/blob/stable/yoga/nova/objects/instance.py#L107)

- **Flavor**: [https://github.com/openstack/nova/blob/stable/yoga/nova/objects/flavor.py#L197](https://github.com/openstack/nova/blob/stable/yoga/nova/objects/flavor.py#L197)

## Validator

Nova API unterstützt die Validierung von Flavor Extra Specs.

Dazu muss die Funktion **register** implementiert werden, die eine Liste an Validator zurückliefert. In diesem Projekt sind die Validator unter **src/schedulerbuilder/nova/validators.py** implementiert.

Der folgende Python Code zeigt ein Beispiel welches zwei Extra Spec Attribute validiert.

```python
from nova.api.validation.extra_specs import base

def register():
    validators = [
        base.ExtraSpecValidator(
            name='customscope:someattribute',
            description='Custom Enum Attribute that is used in filter/weighers',
            value={
                'type': str,
                'enum': [
                   'optionA',
                   'optionB'
                ]
            }
        ),
        base.ExtraSpecValidator(
            name='customscope:anotherattribute',
            description='Custom int Attribute',
            value={
                'type': int
            }
        )
    ]

    return validators

```

Die Python-Datei muss dann als **nova.api.extra_spec_validators** Entrypoint registriert werden [[1]](#quelle_1).

```ini
[options.entry_points]
    nova.api.extra_spec_validators =
        customscope = namespace.of.my.package.validator
```

**Die Validierung wird ab der Nova Compute API Version 2.86 unterstützt [[3]](#quelle_3).** Eine ältere API Version, welche zum Beispiel auch von Horizon genutzt wird, akzeptiert alle Werte. Eine Validierung findet dort nicht statt.

Über die OpenStack CLI kann die API Version manuell gesetzt werden:

```bash
openstack --os-compute-api-version 2.86 flavor set --property customattribute:someattribute=optionA $FLAVOR # OK
openstack --os-compute-api-version 2.86 flavor set --property customattribute:someattribute=invalid $FLAVOR # FAIL
openstack flavor set --property customattribute:someattribute=invalid $FLAVOR # OK
```

## Tests

Dieses Projekt stellt Unit-Tests unter **tests/unit** bereit. Diese können mit `tox` ausgeführt werden.

## Quellen

<a id="quelle_1">[1]</a>
<https://docs.openstack.org/nova/yoga/admin/scheduling.html>

<a id="quelle_2">[2]</a>
<https://wiki.openstack.org/wiki/Scheduler/NormalizedWeights>

<a id="quelle_3">[3]</a>
<https://github.com/openstack/nova/blob/stable/yoga/nova/api/openstack/api_version_request.py#L234>
