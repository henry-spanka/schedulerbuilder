from nova.api.validation.extra_specs import base
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

def register():
    validators = [
        base.ExtraSpecValidator(
            name='gpu_weigher:enabled',
            description='Enable GPU weighing.',
            value={
                'type': bool
            }
        ),
        base.ExtraSpecValidator(
            name='gpu_weigher:mode',
            description='Weighing mode - push or pull nodes',
            value={
                'type': str,
                'enum': [
                    'pull',
                    'push'
                ]
            }
        ),
        base.ExtraSpecValidator(
            name='gpu_weigher:resource',
            description='Resource to use for weighing.',
            value={
                'type': str
            }
        )
    ]

    return validators
