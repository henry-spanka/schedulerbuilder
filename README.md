# schedulerbuilder

Schedulerbuilder ist ein Projekt zur Entwicklung und Testen von Nova Scheduler Filter und Weigher.

Es wurde im Rahmen einer Bachelorarbeit an der Universität Bielefeld entwickelt.

## Anforderungen

Zur Entwicklung von Nova Scheduler Filtern werden mehrere Server benötigt.

Dabei setzt sich die minimale Entwicklungsumgebung aus den folgenden Komponenten zusammen:

- 2x Compute Node zur Erzeugung von virtuellen Maschinen
- 1x Controller Node für die Basis-Dienste des Openstack Clusters
- 1x Entwicklungs Node

Die Server können dabei virtualisiert betrieben werden. In besonderen Fällen müssen die Compute Nodes auf physischer Hardware laufen, wenn zum Beispiel bestimmte Hardware zum Scheduling verwendet werden soll.

Im Rahmen der Bachelorarbeit wurden dabei folgende virtuelle Instanzen zur Entwicklung genutzt:

- 2x Compute Nodes
  - 1 vCPU
  - 2 GB RAM

- 1x Controller Node
  - 4 vCPUs
  - 8 GB RAM

- 1x Entwicklungs Node
  - 1 vCPU
  - 2 GB RAM

Die Controller und Compute Nodes müssen dabei über zwei Netzwerk Interfaces verfügen. Das Erste wird für die Kommunikation zwischen OpenStack Komponenten und Konfiguration verwendet.
Ein zweites Interface ist für die Bereitstellug von Netzwerkdiensten für die OpenStack Instanzen (Neutron) notwendig. Eine IP-Adresse sollte dafür nicht auf dem Interface konfiguriert sein.

Als Betriebssystem wurde für alle Nodes Ubuntu 20.04.4 LTS mit dem OpenStack Release Yoga genutzt.

## Installation einer OpenStack Entwicklungsumgebung

Unter [docs/installation-openstack.md](docs/installation-openstack.md) wird die Installation einer Entwicklungsumgebung der OpenStack Cloud beschrieben.

## Installation von Filtern und Weigher

Die Installation dieses Projektes und eigenen Filtern in einer Openstack Entwicklungsumgebung ist unter [docs/installation-scheduler.md](docs/installation-scheduler.md) beschrieben.

## Entwicklung von Filter und Weigher

Die Erweiterung dieses Projektes um Filter und Weigher ist unter [docs/scheduler.md](docs/scheduler.md) beschrieben.

## Erweiterung von Placement um Ressourceklassen

OpenStack Nova bietet die Erweiterung von Placement Ressourceklassen mit Hilfe von Resource Providern an. Eine Anleitung für die Ressourcenklasse CUSTOM_GPU ist unter
[docs/resourceclass.md](docs/resourceclass.md) hinterlegt.

## Projekt bauen

Alle Abhängigkeiten können mit dem Befehl `pip install -e .` installiert werden.
Gebaut werden kann das Projekt dann mit `tox -e build`. Die Artefakte sind dann im Ordner **dist/** zu finden.

## Tests

Unit Tests für Filter und Weigher sind im Ordner **tests/unit** zu finden. Die Tests können mit dem Befehl **tox** ausgeführt werden.

## Lizenz

Der Quellcode ist verfügbar unter der MIT Lizenz die unter [LICENSE.txt](LICENSE.txt) eingesehen werden kann.

## Note

This project has been set up using PyScaffold 4.2.1. For details and usage
information on PyScaffold see <https://pyscaffold.org/>.
