# -*- coding: utf-8 -*-
u"""@package senml.senml
SenML Python object representation

@todo Add CBOR support
"""

import attr


class SenMLMeasurement(object):
    u"""SenML data representation"""
    name = attr.ib(default=None)
    time = attr.ib(default=None)
    unit = attr.ib(default=None)
    value = attr.ib(default=None)
    sum = attr.ib(default=None)

    def to_absolute(self, base):
        u"""Convert values to include the base information

        Be aware that it is not possible to compute time average of the signal
        without the base object since the base time and base value are still
        needed for that use case."""
        attrs = {
            u'name': (base.name or u'') + (self.name or u''),
            u'time': (base.time or 0.0) + (self.time or 0.0),
            u'unit': self.unit or base.unit,
            u'sum': self.sum,
        }
        if isinstance(self.value, (bool, str, unicode)):
            attrs[u'value'] = self.value
        elif self.value is not None:
            attrs[u'value'] = (base.value or 0.0) + (self.value or 0.0)

        ret = self.__class__(**attrs)
        return ret

    @classmethod
    def base_from_json(cls, data):
        u"""Create a base instance from the given SenML data"""
        template = cls()
        attrs = {
            u'name': data.get(u'bn', template.name),
            u'time': data.get(u'bt', template.time),
            u'unit': data.get(u'bu', template.unit),
            u'value': data.get(u'bv', template.value),
        }
        return cls(**attrs)

    @classmethod
    def from_json(cls, data):
        u"""Create an instance given JSON data as a dict"""
        template = cls()
        attrs = {
            u'name': data.get(u'n', template.name),
            u'time': data.get(u't', template.time),
            u'unit': data.get(u'u', template.unit),
            u'value': data.get(u'v', template.value),
            u'sum': data.get(u's', template.sum),
        }
        if attrs[u'value'] is None:
            if u'vs' in data:
                attrs[u'value'] = unicode(data[u'vs'])
            elif u'vb' in data:
                attrs[u'value'] = bool(data[u'vb'])
            elif u'vd' in data:
                attrs[u'value'] = str(data[u'vd'])

        return cls(**attrs)

    def to_json(self):
        u"""Format the entry as a SenML+JSON object"""
        ret = {}
        if self.name is not None:
            ret[u'n'] = unicode(self.name)

        if self.time is not None:
            ret[u't'] = float(self.time)

        if self.unit is not None:
            ret[u'u'] = unicode(self.unit)

        if self.sum is not None:
            ret[u's'] = float(self.sum)

        if isinstance(self.value, bool):
            ret[u'vb'] = self.value
        elif isinstance(self.value, str):
            ret[u'vd'] = self.value
        elif isinstance(self.value, unicode):
            ret[u'vs'] = self.value
        elif self.value is not None:
            ret[u'v'] = float(self.value)

        return ret


SenMLMeasurement = attr.s(SenMLMeasurement)


class SenMLDocument(object):
    u"""A collection of SenMLMeasurement data points"""

    measurement_factory = SenMLMeasurement

    def __init__(self, measurements=None, *args, **kwargs):
        u"""
        Constructor
        """
        if u'base' in kwargs:
            base = kwargs[u'base']
            del kwargs[u'base']
        else:
            base = None
        super(SenMLDocument, self).__init__(*args, **kwargs)
        self.measurements = measurements
        self.base = base

    @classmethod
    def from_json(cls, json_data):
        u"""Parse a loaded SenML JSON representation into a SenMLDocument

        @param[in] json_data  JSON list, from json.loads(senmltext)
        """
        # Grab base information from first entry
        base = cls.measurement_factory.base_from_json(json_data[0])

        measurements = [cls.measurement_factory.from_json(item) for item in json_data]

        obj = cls(base=base, measurements=measurements)

        return obj

    def to_json(self):
        u"""Return a JSON dict"""
        first = {
            # Add SenML version
            u'bver': 5,
        }
        if self.base:
            base = self.base

            if base.name is not None:
                first[u'bn'] = unicode(base.name)
            if base.time is not None:
                first[u'bt'] = float(base.time)
            if base.unit is not None:
                first[u'bu'] = unicode(base.unit)
            if base.value is not None:
                first[u'bv'] = float(base.value)

        if self.measurements:
            first.update(self.measurements[0].to_json())
            ret = [first]
            ret.extend([item.to_json() for item in self.measurements[1:]])
        else:
            ret = []

        return ret

    def to_absolute_json(self):
        u"""
        Return a JSON dict
        """
        return [item.to_absolute(self.base).to_json() for item in self.measurements if item.name is not None]
