from openstack.object_store.v1.container import Container as _Container


class Container(_Container):
    # TODO: Delete custom dunderinit (01/2019)
    # The _connection attribute doesn't exist in OpenStack SDK 0.9.x
    # However, it does in latter versions. Hence, we can reuse it when
    # Rackspace SDK will be compatible with more recent versions of OpenStack
    # SDK.
    def __init__(self, attrs=None, loaded=False, connection=None):
        self._connection = connection
        super().__init__(**attrs)

    @classmethod
    def existing(cls, connection=None, **kwargs):
        return cls(kwargs, loaded=True, connection=connection)
