"""Internal handles for authored placements without an ActionScript name."""


def instance_key(placement: dict) -> str:
    if placement.get('name'):
        return placement['name']
    # Reserve a handle outside the source's identifier queries. Keep the source
    # display list untouched; materialization labels these as internal handles.
    return '@placement:%s:%s:%s' % (
        placement['depth'], placement['character_id'], placement['placed_frame'])
