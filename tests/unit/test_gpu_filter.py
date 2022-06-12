import mock
from oslo_utils.fixture import uuidsentinel as uuids

from nova import objects
from schedulerbuilder.nova.filters.virtual_filter import GpuVirtualFilter
from nova import test
from nova.tests.unit.scheduler import fakes

__author__ = "Henry Spanka"
__copyright__ = "Henry Spanka"
__license__ = "MIT"


@mock.patch('nova.scheduler.filters.utils.aggregate_metadata_get_by_host')
class TestGpuFilter(test.NoDBTestCase):

    def setUp(self):
        super(TestGpuFilter, self).setUp()
        self.filt_cls = GpuVirtualFilter()

    def test_gpu_filter_passes_no_extra_specs(self, agg_mock):
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            flavor=objects.Flavor())
        host = fakes.FakeHostState('host1', 'node1', {})
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))

    def _do_test_gpu_filter_extra_specs(self, especs, passes, instances=[]):
        spec_obj = objects.RequestSpec(
            context=mock.sentinel.ctx,
            flavor=objects.Flavor(extra_specs=especs),
            num_instances=1)
        host = fakes.FakeHostState('host1', 'node1', {})

        host.instances = {instance.uuid: instance for instance in instances}

        assertion = self.assertTrue if passes else self.assertFalse
        assertion(self.filt_cls.host_passes(host, spec_obj))

    def _make_instance(self, name, enabled, model, count):
        flavor = objects.Flavor(extra_specs={
            'gpu_filter:enabled': 'true' if enabled else 'false',
            'gpu_filter:model': model,
            'gpu_filter:count': count
        })

        return objects.Instance(uuid=getattr(uuids, name), flavor=flavor)

    def test_gpu_filter_passes_empty_extra_specs(self, agg_mock):
        self._do_test_gpu_filter_extra_specs(
            especs={},
            passes=True)

    def test_gpu_filter_fails_without_model(self, agg_mock):
        self._do_test_gpu_filter_extra_specs(
            especs={'gpu_filter:enabled': 'true', 'gpu_filter:count': '2'},
            passes=False)

    def test_gpu_filter_fails_without_count(self, agg_mock):
        self._do_test_gpu_filter_extra_specs(
            especs={'gpu_filter:enabled': 'true', 'gpu_filter:model': 'quadro'},
            passes=False)

    def test_gpu_filter_passes_fit(self, agg_mock):
        agg_mock.return_value = {'gpu_filter:model': set(
            ['quadro']), 'gpu_filter:count': set(['4'])}
        self._do_test_gpu_filter_extra_specs(
            especs={'gpu_filter:enabled': 'true',
                    'gpu_filter:model': 'quadro', 'gpu_filter:count': '2'},
            passes=True)

    def test_gpu_filter_passes_fit_exact(self, agg_mock):
        agg_mock.return_value = {'gpu_filter:model': set(
            ['quadro']), 'gpu_filter:count': set(['4'])}
        self._do_test_gpu_filter_extra_specs(
            especs={'gpu_filter:enabled': 'true',
                    'gpu_filter:model': 'quadro', 'gpu_filter:count': '2'},
            passes=True, instances=[
                self._make_instance('instance1', True, 'quadro', '1'),
                self._make_instance('instance2', True, 'quadro', '1')])

    def test_gpu_filter_passes_fit_ignore_other_model(self, agg_mock):
        agg_mock.return_value = {'gpu_filter:model': set(
            ['quadro']), 'gpu_filter:count': set(['4'])}
        self._do_test_gpu_filter_extra_specs(
            especs={'gpu_filter:enabled': 'true',
                    'gpu_filter:model': 'quadro', 'gpu_filter:count': '2'},
            passes=True, instances=[
                self._make_instance('instance1', True, 'quadro', '1'),
                self._make_instance('instance2', True, 'tesla', '2')])

    def test_gpu_filter_passes_no_gpus_disabled(self, agg_mock):
        agg_mock.return_value = {'gpu_filter:model': set(
            ['quadro']), 'gpu_filter:count': set(['0'])}
        self._do_test_gpu_filter_extra_specs(
            especs={'gpu_filter:enabled': 'false',
                    'gpu_filter:model': 'quadro', 'gpu_filter:count': '1'},
            passes=True)

    def test_gpu_filter_fails_no_gpus(self, agg_mock):
        agg_mock.return_value = {'gpu_filter:model': set(
            ['quadro']), 'gpu_filter:count': set(['0'])}
        self._do_test_gpu_filter_extra_specs(
            especs={'gpu_filter:enabled': 'true',
                    'gpu_filter:model': 'quadro', 'gpu_filter:count': '1'},
            passes=False)

    def test_gpu_filter_fails_no_fit(self, agg_mock):
        agg_mock.return_value = {'gpu_filter:model': set(
            ['quadro']), 'gpu_filter:count': set(['4'])}
        self._do_test_gpu_filter_extra_specs(
            especs={'gpu_filter:enabled': 'true',
                    'gpu_filter:model': 'quadro', 'gpu_filter:count': '2'},
            passes=False, instances=[
                self._make_instance('instance1', True, 'quadro', '1'),
                self._make_instance('instance2', True, 'quadro', '2')])
