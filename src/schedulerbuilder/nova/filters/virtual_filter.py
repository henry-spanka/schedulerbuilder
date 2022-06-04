from oslo_log import log as logging
from nova.scheduler import filters
from nova.objects.request_spec import RequestSpec
from nova.scheduler.host_manager import HostState
from schedulerbuilder.nova import extraSpecIsTrue, getAggregateMetadataUnique, getExtraSpecsValue
from nova.scheduler.filters import utils as filterUtils
from nova.objects.instance import Instance

LOG = logging.getLogger(__name__)

_SCOPE = 'gpu_weigher'

class GpuVirtualFilter(filters.BaseHostFilter):

    RUN_ON_REBUILD = False

    def host_passes(self, host_state: HostState, request_spec: RequestSpec):
        if not extraSpecIsTrue(request_spec.flavor, 'enabled', _SCOPE):
            # If GPU filtering is disabled the host passes.
            return True

        model = getAggregateMetadataUnique(host_state, 'model', _SCOPE)
        count = getAggregateMetadataUnique(host_state, 'count', _SCOPE)

        if model is None or count is None:
            LOG.debug("Host has either gpu model or count not defined. Not considering a viable host.")
            return False

        # convert GPU count to int after validation to ensure this is not None
        count = int(count)

        requestModel = getExtraSpecsValue(request_spec.flavor, 'model', _SCOPE)
        requestCount = getExtraSpecsValue(request_spec.flavor, 'count', _SCOPE)

        if requestModel is None or requestModel != model:
            LOG.debug("Host does not match requested GPU model.")
            return False
        
        if requestCount is None:
            LOG.warning("Requested GPU Count not defined. This is unsupported.")
            return False

        count -= int(requestCount) * int(request_spec.num_instances) if extraSpecIsTrue(request_spec.flavor, 'samehost', _SCOPE) else 1

        if count < 0:
            # host has more total GPUs than the flavor requested.
            return False

        # Calculate in use GPU count by instances on the host
        Instance: Instance
        for (_, instance) in host_state.instances.items():
            if extraSpecIsTrue(instance.flavor, 'enabled', _SCOPE):
                # GPU Weighing is enabled on this instance
                instanceModel = getExtraSpecsValue(instance.flavor, 'model', _SCOPE)
                instanceCount = getExtraSpecsValue(instance.flavor, 'count', _SCOPE)

                if instanceModel != model:
                    LOG.warning("Instance GPU model does not match configured host GPU model. \
                        This should not happen under normal circumstances. Ignoring for calculation.")
                    continue
                if instanceCount is None:
                    LOG.warning("Instance GPU count not defined. \
                        This should not happen under normal circumstances. Ignoring for calculation.")
                    continue

                count -= int(instanceCount)

        # count is >= 0 when all instances fit on the host including the scheduled one.
        return count >= 0
