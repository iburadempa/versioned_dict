A versioned dictionary class derived from the native *dict* class.

Hint: Only runs with Python3!

This class is useful when subsequent versions of a dictionary frequently
have common key-value pairs which consume quite some memory or would be
time-consuming to deep-copy for each new version.

When 'archiving' a version, only the difference relative to the last stored
version is put on the archive stack (kind of incremental backup):
Added keys and their values, deleted keys and their values and modified keys
and their values are are stored.

Limitations::
  * If rewinding of versions happens very often, this approach
    lacks performance, in particular when there are many versions.
  * When archiving a version, the difference is examined only on the highest
    level: In case of a common key the substructure of the values is not
    examined. (That would somewhat correspond to a differential backup.)
  * When rewinding or looking up a specific archived version, the item
    ordering is usually not preserved (as is not to be expected from a
    :class:`dict`).
  * keys are assumed to objects of type :class:`str`. We do deep-copy keys
    when archiving, but this is not tested.

Example use case: Version 0 of the dictionary has just one key containing the
fulltext of a longer document. Other versions add or delete keys containing
intermediate results in analyzing the document, which may themselves be of
considerable size, but which don't change the document.

There is no documentation beyond the unit tests.
