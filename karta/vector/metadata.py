""" Vector geospatial metadata management """

import copy
import numbers
from collections import Mapping
import numpy
IntegerType = (numbers.Integral, numpy.int32, numpy.int64)

class Metadata(Mapping):
    """ Class for handling collections of metadata. Data are organized similar
    to a Python dict, however different values must all have the same length
    and be of uniform type.

    Data are accessed either by field name (returning the entire series for
    that field) for by index (returning the value within eather field at that
    index). """

    _data = {}
    _fieldtypes = []

    def __init__(self, data, singleton=False):
        """ Create a collection of metadata from *data*, which may be a list
        with uniform type or a dictionary with equally-sized fields of uniform
        type.

        Parameters
        ----------
        data : list of uniform type or dictionary of equally-sized fields of
        uniform type

        *kwargs*:
        singleton : treat data as a single unit, rather than as a list of units
        """

        if singleton:

            if hasattr(data, "keys") and hasattr(data.values, "__call__"):
                self._data = data
            elif data is not None:
                self._data = {"values": data}
            else:
                self._data = {}
            self._fieldtypes = [type(self._data[k]) for k in self._data]
            self._len = 1

        else:

            if hasattr(data, 'keys') and hasattr(data.values, '__call__'):
                # Dictionary of attributes
                for k in data:
                    dtype = type(data[k][0])
                    if False in (isinstance(a, dtype) for a in data[k]):
                        raise MetadataError("Data must have uniform type")
                    n = len(data[k])

                if False in (len(data[k]) == n for k in data):
                    raise MetadataError("Data must have uniform lengths")
                elif len(data) == 0:
                    self._len = 0
                else:
                    self._len = n

            elif data is not None:
                # Single attribute
                if not hasattr(data, '__iter__'):
                    data = [data]
                self._len = len(data)
                dtype = type(data[0])
                if False in (isinstance(a, dtype) for a in data):
                    raise MetadataError("Data must have uniform type")
                else:
                    data = {'values': data}

            else:
                # No metadata
                data = {}
                self._len = 0

            self._data = data
            self._fieldtypes = [type(data[k][0]) for k in data]
        return

    def __repr__(self):
        return "D[" + ", ".join(str(k) for k in self._data.keys()) + "]"

    def __add__(self, other):
        if not isinstance(other, type(self)):
            raise MetadataError("self and other must both be instances of {0}".format(type(self)))
        if set(self.keys()) != set(other.keys()):
            raise MetadataError("self and other do not have identical field names")
        res = copy.deepcopy(self)
        res._len += other._len
        for k in res:
            res[k] += other[k]
        return res

    def __len__(self):
        return self._len

    def __contains__(self, other):
        return (other in self._data)

    def __iter__(self):
        return self._data.__iter__()

    def __setitem__(self, key, value):
        if isinstance(key, (IntegerType, slice)):
            #       if len(self._fieldtypes) == 1:
            #           return self.values()[0][key]
            #       else:

            nkeys = len(self._data.keys())
            if (nkeys > 1) and (nkeys != len(list(value))):
                raise IndexError("Setting Metadata requires a value to be "
                                 "provided for every Metadata field")

            if nkeys > 1:
                for seq in self._data.values():
                    seq[key] = value[key]
            else:
                for k in self._data.keys():
                    self._data[k][key] = value

        else:
            if len(list(value)) != len(self):
                raise IndexError("Setting a Metadata field requires that "
                                 "length be preserved")
            self._data[key] = list(value)
        return

    def __getitem__(self, key):
        # If there is one field type, a number index should return a scalar
        # If there are multiple field types, a number index should return a dict
        # Although this is a bit irregular, it probably adheres better to the
        # principle of least surprise
        if isinstance(key, (IntegerType, slice)):
            return dict((k, self._data[k][key]) for k in self._data.keys())
        else:
            return self.getfield(key)

    def __delitem__(self, idx):
        for k in self._data:
            del self._data[k][idx]
        self._len -= 1

    def sub(self, idxs):
        """ Return a Metadata instance with values from idxs. """
        newdata = dict()
        try:
            items = self._data.iteritems()
        except AttributeError:
            items = self._data.items()

        for key, val in items:
            newdata[key] = [self._data[key][i] for i in idxs]
        return Metadata(newdata)

    def getfield(self, name):
        """ Return all values from field *name*. """
        if name not in self._data:
            raise IndexError("Field {0} not in Metadata".format(name))
        return self._data[name]

    def extend(self, other):
        """ Extend collection in-place. """
        if isinstance(other, type(self)):
            for i, k in enumerate(self._data):
                if type(self._fieldtypes[i]) == type(other._fieldtypes[i]):
                    self._data[k] += other._data[k]
                    self._len += other._len
                else:
                    raise MetadataError("Cannot combine metadata instances "
                                         "with different type hierarchies")
        return self

    def keys(self):
        """ Return internal dictionary keys. """
        return self._data.keys()

    def values(self):
        """ Return internal dictionary values. """
        return self._data.values()


class MetadataError(Exception):
    def __init__(self, message=''):
        self.message = message
    def __str__(self):
        return self.message

