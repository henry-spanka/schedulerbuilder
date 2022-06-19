# Installation der OpenStack Entwicklungsumgebung

Im folgenden wird davon ausgegangen, dass sich alle Nodes auf dem Interface *eth0* untereinander erreichen können. Das weitere Interface *eth1* befindet sich in einem separaten Segment und besitzt keine IP-Adresse.

Die Schritte [[1]](#quelle_1) werden dabei alle auf der Deployment Node ausgeführt.

## Installation von OpenStack Kolla

1. Installation von Abhängigkeiten.

  ```bash
  sudo apt install python3-dev libffi-dev gcc libssl-dev
  ```

2. Installation vom Python Paket Manager.

  ```bash
  sudo apt install python3-pip
  ```

3. Sicherstellen dass die aktuelle Version installiert ist.

  ```bash
  sudo pip3 install -U pip
  ```

4. Installation von Ansible.

  ```bash
  sudo apt install ansible
  ```

5. Installation von Kolla-Ansible.

  ```bash
  sudo pip3 install git+https://opendev.org/openstack/kolla-ansible@stable/yoga
  ```

6. Erstellen vom **/etc/kolla** Verzeichnis.

  ```bash
  sudo mkdir -p /etc/kolla
  sudo chown $USER:$USER /etc/kolla
  ```

7. Kopieren von **globals.yml** und **passwords.yml** nach **/etc/kolla**

  ```bash
  cp -r /usr/local/share/kolla-ansible/etc_examples/kolla/* /etc/kolla
  ```

8. Kopieren des **all-in-one** und **multinode** Inventories.

  ```bash
  cp /usr/local/share/kolla-ansible/ansible/inventory/* .
  ```

9. Installation der Ansible Galaxy Abhängigkeiten.

  ```bash
  kolla-ansible install-deps
  ```

Eventuell tritt bei Schritt 9 folgender Fehler auf:
```bash
root@deployment:~# kolla-ansible install-deps
ERROR: Ansible version should be between 2.11 and 2.12. Current version is 2.9.6 which is not supported
````

Dann ist die Ansible Version inkompatibel mit Kolla. Ansible muss dann deinstalliert (`sudo apt purge ansible`) und als Pip Paket installiert werden (`sudo pip install -U 'ansible>=4,<6'`)

## Konfiguration von Ansible

Zur besseren Performance von Ansible sollte folgende Konfiguration zur Datei **/etc/ansible.cfg** hinzugefügt werden.

```ini
[defaults]
host_key_checking=False
pipelining=True
forks=100
```

## Initiale Konfiguration

### Ansible Inventory

Zuerst müssen Controller und Compute Nodes die entsprechenden Rollen im Ansible Inventory zugewiesen werden.

Dabei wird das Inventory **multinode** verwendet, da zur Entwicklung von Filtern mindestens zwei Compute Nodes notwendig sind.

1. Die erste Sektion wird wie folgt angepasst.

  ```ini
  # These initial groups are the only groups required to be modified. The
  # additional groups are for more control of the environment.
  [control]
  # These hostname must be resolvable from your deployment host
  controller

  # The network nodes are where your l3-agent and loadbalancers will run
  # This can be the same as a host in the control group
  [network]
  controller

  [compute]
  compute1
  compute2
  # ggf. weitere compute nodes

  [monitoring]
  controller

  [storage]
  controller

  [deployment]
  localhost       ansible_connection=local
  ```

2. Zusätzlich müssen alle Hosts mit ihrer IP-Adresse vom Interface **eth0** in **/etc/hosts** eingetragen werden, damit die Deployment Node die anderen Nodes über ihren Hostnamen erreichen kann.

  ```text
  192.168.10.3 controller
  192.168.10.4 compute1
  192.168.10.5 compute2
  ```

3. Es wird geprüft ob alle Nodes erreicht werden können. Sollte dabei ein Fehler auftreten, muss eventuell erst ein SSH Keypair erzeugt werden und der Public-Key auf den anderen Nodes installiert werden (siehe Linux Befehl ssh-copy-id).

  ```bash
  ansible -i multinode all -m ping
  ```

### Kolla Passwörter

Alle Passwörter der OpenStack Umgebung werden in der Datei **/etc/kolla/passwords.yml** gespeichert. Standardgemäß sind die Passwörter leer und müssen manuell gesetzt werden. Alternativ können die Passwörter automatisch generiert werden.

1. Befehl zur automatischen Generierung von Passwörtern.

  ```bash
  kolla-genpwd
  ```

## Kolla globals.yml

Die **/etc/kolla/globals.yml** ist die Haupt Konfigurations-Datei von OpenStack Kolla.

Folgende Änderungen müssen darin vorgenommen werden.

1. Setzen der Container-Umgebung auf **ubuntu**.

  ```ini
  kolla_base_distro: "ubuntu"
  ```

2. Konfiguration der IP Addresse unter der die OpenStack Dienste erreichbar sind. Hier ist die IP des Interfaces **eth0** der Controller Node einzutragen.

  ```ini
  kolla_internal_vip_address: "192.168.10.3"
  ```

3. Deaktivierung von Haproxy.

  ```ini
  enable_haproxy: "no"
  ````

4. Setzen des Cluster und Neutron Netzwerkinterfaces.

  ```ini
  network_interface: "eth0"
  neutron_external_interface: "eth1"
  ```

5. (Optional) Aktivieren des Debug Loggings aller OpenStack Dienste.

  ```ini
  openstack_logging_debug: "True"
  ```

## Deployment der OpenStack Cloud

Installation und Konfiguration der OpenStack Nodes.

1. Kolla Deploy Abhängigkeiten installieren.

  ```bash
  kolla-ansible -i ./multinode bootstrap-servers
  ```

2. Validierung der Umgebung und Konfiguration.

  ```bash
  kolla-ansible -i ./multinode prechecks
  ````

3. Installation der OpenStack Umgebung.

  ```bash
  kolla-ansible -i ./multinode deploy
  ```

Nach erfolgreicher Installation ist das OpenStack Horizon Web Panel erreichbar (hier `http://192.168.10.3`).

Die Zugangsdaten lassen sich in **/etc/kolla/passwords.yml** oder mit folgendem Befehl finden.

```bash
cat /etc/kolla/passwords.yml | grep 'keystone_admin_password'
```

Entsprechende Fehlermeldungen und Fehlerquellen sind im [Troubleshooting Guide](https://docs.openstack.org/kolla-ansible/yoga/user/troubleshooting.html) beschrieben.

## Initiale Einrichtung der OpenStack Cloud

Standardgemäß sind keine Ports, Subnetze oder Flavors eingerichtet. Kolla bietet eine Standardkonfiguration die einige Flavors beinhaltet. Dieser Schritt ist optional, sollte aber ausgeführt werden um eine Basiskonfiguration zu erhalten.

1. Installation des OpenStack CLI Clients.

  ```bash
  sudo pip install python-openstackclient -c https://releases.openstack.org/constraints/upper/yoga
  # Alternativ falls die Installation fehlschlägt
  sudo apt install python3-openstackclient
  ````

2. Generierung der OpenStack **openrc** Datei die Zugangsdaten für die OpenStack API enthält.

  ```bash
  kolla-ansible post-deploy
  . /etc/kolla/admin-openrc.sh
  ```

3. Anlegen der Basiskonfiguration.

  ```bash
  /usr/local/share/kolla-ansible/init-runonce
  ```
  
## Quellen

<a id="quelle_1">[1]</a>
<https://docs.openstack.org/kolla-ansible/yoga/user/quickstart.html>
