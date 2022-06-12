from oslo_utils.fixture import uuidsentinel as uuids

from nova import objects
from nova.scheduler import weights
from schedulerbuilder.nova.weighers.virtual_weigher import GpuVirtualWeigher
from nova import test
from nova.tests.unit.scheduler import fakes

__author__ = "Henry Spanka"
__copyright__ = "Henry Spanka"
__license__ = "MIT"


class TestGpuWeigher(test.NoDBTestCase):

    def setUp(self):
        super(TestGpuWeigher, self).setUp()

        self.weight_handler = weights.HostWeightHandler()
        self.weighers = [GpuVirtualWeigher()]
        self.filt_cls = GpuVirtualWeigher()

    def _get_weighed_hosts(self, hosts, weight_properties=None):
        if weight_properties is None:
            weight_properties = {}
        return self.weight_handler.get_weighed_objects(self.weighers,
                                                       hosts, weight_properties)

    def _make_instance(self, name, count, key='resources:CUSTOM_GPU'):
        flavor = objects.Flavor(extra_specs={
            key: count
        })

        return objects.Instance(uuid=getattr(uuids, name), flavor=flavor)

    def _convert_instances(self, instances):
        return {instance.uuid: instance for instance in instances}

    def _make_spec(self, especs):
        return objects.RequestSpec(
            flavor=objects.Flavor(extra_specs=especs))

    def _get_all_hosts(self):
        instances1 = [self._make_instance(
            'instance1', '2'), self._make_instance('instance2', '1')]
        instances2 = [self._make_instance('instance3', '2')]
        instances3 = [self._make_instance(
            'instance4', '1'), self._make_instance('instance5', '1', 'otherkey')]

        host_values = [
            ('host1', 'node1', {'instances': self._convert_instances(instances1)}),
            ('host2', 'node2', {'instances': self._convert_instances(instances2)}),
            ('host3', 'node3', {'instances': self._convert_instances(instances3)}),
            ('host4', 'node4', {})
        ]
        return [fakes.FakeHostState(host, node, values)
                for host, node, values in host_values]

    def test_gpu_weigher_same_no_extra_specs(self):
        hostinfo_list = self._get_all_hosts()

        spec_obj = objects.RequestSpec(
            flavor=objects.Flavor())
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, spec_obj)

        for host in weighed_hosts:
            self.assertEqual(0.0, host.weight)

    def test_gpu_weigher_same_empty_extra_specs(self):
        hostinfo_list = self._get_all_hosts()

        spec_obj = self._make_spec({})
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, spec_obj)

        for host in weighed_hosts:
            self.assertEqual(0.0, host.weight)

    def test_gpu_weigher_same_disabled(self):
        hostinfo_list = self._get_all_hosts()

        spec_obj = self._make_spec(
            {'gpu_weigher:enabled': 'false', 'gpu_weigher:resource': 'resources:CUSTOM_GPU', 'gpu_weigher:mode': 'stack'})
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, spec_obj)

        for host in weighed_hosts:
            self.assertEqual(0.0, host.weight)

    def test_gpu_weigher_same_no_mode(self):
        hostinfo_list = self._get_all_hosts()

        spec_obj = self._make_spec(
            {'gpu_weigher:enabled': 'false', 'gpu_weigher:resource': 'resources:CUSTOM_GPU'})
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, spec_obj)

        for host in weighed_hosts:
            self.assertEqual(0.0, host.weight)

    def test_gpu_weigher_same_no_resource(self):
        hostinfo_list = self._get_all_hosts()

        spec_obj = self._make_spec(
            {'gpu_weigher:enabled': 'false', 'gpu_weigher:mode': 'stack'})
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, spec_obj)

        for host in weighed_hosts:
            self.assertEqual(0.0, host.weight)

    def test_gpu_weigher_same_invalid_mode(self):
        hostinfo_list = self._get_all_hosts()

        spec_obj = self._make_spec(
            {'gpu_weigher:enabled': 'false', 'gpu_weigher:mode': 'something'})
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, spec_obj)

        for host in weighed_hosts:
            self.assertEqual(0.0, host.weight)

    def test_gpu_weigher_stacking(self):
        hostinfo_list = self._get_all_hosts()

        spec_obj = self._make_spec(
            {'gpu_weigher:enabled': 'true', 'gpu_weigher:resource': 'resources:CUSTOM_GPU', 'gpu_weigher:mode': 'stack'})
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, spec_obj)

        # host1 w = 1.0
        # host2 w = 0.66
        # host3 w = 0.33
        # host4 w = 0.0

        self.assertEqual(1.0, weighed_hosts[0].weight)
        self.assertEqual('host1', weighed_hosts[0].obj.host)

        self.assertEqual(float(2/3), weighed_hosts[1].weight)
        self.assertEqual('host2', weighed_hosts[1].obj.host)

        self.assertEqual(float(1/3), weighed_hosts[2].weight)
        self.assertEqual('host3', weighed_hosts[2].obj.host)

        self.assertEqual(0.0, weighed_hosts[3].weight)
        self.assertEqual('host4', weighed_hosts[3].obj.host)

    def test_gpu_weigher_spreading(self):
        hostinfo_list = self._get_all_hosts()

        spec_obj = self._make_spec(
            {'gpu_weigher:enabled': 'true', 'gpu_weigher:resource': 'resources:CUSTOM_GPU', 'gpu_weigher:mode': 'spread'})
        weighed_hosts = self._get_weighed_hosts(hostinfo_list, spec_obj)

        # host1 w = 0.0
        # host2 w = 0.33
        # host3 w = 0.66
        # host4 w = 1.0

        self.assertEqual(1.0, weighed_hosts[0].weight)
        self.assertEqual('host4', weighed_hosts[0].obj.host)

        self.assertEqual(float(2/3), weighed_hosts[1].weight)
        self.assertEqual('host3', weighed_hosts[1].obj.host)

        self.assertEqual(float(1/3), weighed_hosts[2].weight)
        self.assertEqual('host2', weighed_hosts[2].obj.host)

        self.assertEqual(0.0, weighed_hosts[3].weight)
        self.assertEqual('host1', weighed_hosts[3].obj.host)
